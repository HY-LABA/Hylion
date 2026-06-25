#!/usr/bin/env python3
"""HuggingFace 데이터셋의 특정 에피소드를 gesture 포맷으로 변환·저장.

사용:
  python fetch_hf_gesture.py --gesture pick_object
  python fetch_hf_gesture.py --gesture pick_object --episode 5  # 특정 에피소드

기본값:
  --repo    BaboGaeguri/leftarm_v2
  --episode 마지막 에피소드
  --output  ~/Hylion/jetson/arm/data
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download


def download(repo: str, filename: str) -> Path:
    return Path(hf_hub_download(repo_id=repo, filename=filename, repo_type="dataset"))


def main() -> int:
    ap = argparse.ArgumentParser(description="HF 마지막 에피소드 → gesture 포맷 변환")
    ap.add_argument("--repo",    default="BaboGaeguri/leftarm_v2")
    ap.add_argument("--gesture", required=True, help="저장할 gesture 이름 (snake_case)")
    ap.add_argument("--episode", type=int, default=None, help="에피소드 인덱스 (기본: 마지막)")
    ap.add_argument("--output",  default=str(Path.home() / "Hylion/jetson/arm/data"))
    ap.add_argument("--force",   action="store_true", help="기존 gesture 덮어쓰기")
    args = ap.parse_args()

    gesture_dir = Path(args.output).expanduser() / args.gesture
    if gesture_dir.exists():
        if not args.force:
            print(f"[fetch] 이미 존재: {gesture_dir}  (덮어쓰려면 --force)", file=sys.stderr)
            return 2
        shutil.rmtree(gesture_dir)

    # ── 1. info.json ──────────────────────────────────────────────────────────
    print(f"[fetch] {args.repo} info.json 다운로드 중...")
    info = json.loads(download(args.repo, "meta/info.json").read_text())
    total_episodes = info["total_episodes"]
    fps            = info["fps"]
    action_names   = info["features"]["action"]["names"]
    print(f"[fetch] total_episodes={total_episodes}  fps={fps}")
    print(f"[fetch] action_names={action_names}")

    # ── 2. 에피소드 인덱스 결정 ───────────────────────────────────────────────
    ep_idx = (total_episodes - 1) if args.episode is None else args.episode
    if not (0 <= ep_idx < total_episodes):
        print(f"[fetch] ERROR: episode {ep_idx} 범위 초과 (0~{total_episodes-1})", file=sys.stderr)
        return 1
    print(f"[fetch] 타깃 에피소드: {ep_idx} / {total_episodes-1}")

    # ── 3. episodes 메타 → chunk/file 위치 탐색 ──────────────────────────────
    # episodes 메타가 여러 chunk에 분산될 수 있으므로 전체 탐색.
    print("[fetch] 에피소드 메타 탐색 중...")
    from huggingface_hub import list_repo_files
    ep_files = sorted(
        f for f in list_repo_files(args.repo, repo_type="dataset")
        if f.startswith("meta/episodes/") and f.endswith(".parquet")
    )
    print(f"[fetch] episodes 메타 파일 {len(ep_files)}개 발견")

    ep_dict: dict = {}
    for ep_file in ep_files:
        chunk = pq.read_table(download(args.repo, ep_file)).to_pydict()
        if not ep_dict:
            ep_dict = chunk
        else:
            for k, v in chunk.items():
                ep_dict[k].extend(v)

    ep_indices = ep_dict["episode_index"]
    try:
        row_i = ep_indices.index(ep_idx)
    except ValueError:
        print(f"[fetch] ERROR: episode_index={ep_idx} 를 episodes 메타에서 찾지 못했습니다.", file=sys.stderr)
        return 1

    chunk_i = ep_dict["data/chunk_index"][row_i]
    file_i  = ep_dict["data/file_index"][row_i]
    ep_len  = ep_dict["length"][row_i]
    print(f"[fetch] chunk={chunk_i}  file={file_i}  length={ep_len}")

    # ── 4. 데이터 parquet 다운로드 + 필터링 ──────────────────────────────────
    data_filename = f"data/chunk-{chunk_i:03d}/file-{file_i:03d}.parquet"
    print(f"[fetch] 데이터 파일 다운로드: {data_filename}")
    data_table = pq.read_table(download(args.repo, data_filename))

    mask    = pc.equal(data_table.column("episode_index"), ep_idx)
    ep_data = data_table.filter(mask)
    n       = ep_data.num_rows
    print(f"[fetch] 필터링 완료: {n} 프레임")

    if n == 0:
        print("[fetch] ERROR: 필터링 후 프레임 0개", file=sys.stderr)
        return 1

    # ── 5. 컬럼 재정규화 (episode_index=0, frame_index 0-based) ───────────────
    new_table = pa.table({
        "action":            ep_data.column("action"),
        "observation.state": ep_data.column("observation.state"),
        "timestamp":         pa.array([i / fps for i in range(n)], type=pa.float32()),
        "frame_index":       pa.array(list(range(n)),               type=pa.int64()),
        "episode_index":     pa.array([0] * n,                      type=pa.int64()),
        "index":             pa.array(list(range(n)),               type=pa.int64()),
        "task_index":        pa.array([0] * n,                      type=pa.int64()),
    })

    # ── 6. 디렉토리 생성 ──────────────────────────────────────────────────────
    (gesture_dir / "meta" / "episodes" / "chunk-000").mkdir(parents=True)
    (gesture_dir / "data" / "chunk-000").mkdir(parents=True)

    # ── 7. data parquet 저장 ──────────────────────────────────────────────────
    pq.write_table(new_table, gesture_dir / "data" / "chunk-000" / "file-000.parquet")

    # ── 8. meta/info.json ─────────────────────────────────────────────────────
    gesture_info = {
        "codebase_version":    "v3.0",
        "robot_type":          "so_follower",
        "total_episodes":      1,
        "total_frames":        n,
        "total_tasks":         1,
        "chunks_size":         1000,
        "data_files_size_in_mb":  100,
        "video_files_size_in_mb": 200,
        "fps":                 fps,
        "splits":              {"train": "0:1"},
        "data_path":           "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet",
        "video_path":          None,
        "features": {
            "action": {
                "dtype": "float32",
                "names": action_names,
                "shape": [len(action_names)],
            },
            "observation.state": {
                "dtype": "float32",
                "names": action_names,
                "shape": [len(action_names)],
            },
            "timestamp":     {"dtype": "float32", "shape": [1], "names": None},
            "frame_index":   {"dtype": "int64",   "shape": [1], "names": None},
            "episode_index": {"dtype": "int64",   "shape": [1], "names": None},
            "index":         {"dtype": "int64",   "shape": [1], "names": None},
            "task_index":    {"dtype": "int64",   "shape": [1], "names": None},
        },
    }
    (gesture_dir / "meta" / "info.json").write_text(json.dumps(gesture_info, indent=4))

    # ── 9. meta/tasks.parquet ─────────────────────────────────────────────────
    pq.write_table(
        pa.table({
            "task_index": pa.array([0], type=pa.int64()),
            "task":       pa.array([f"{{'Gesture': '{args.gesture}'}}"]),
        }),
        gesture_dir / "meta" / "tasks.parquet",
    )

    # ── 10. meta/episodes parquet (간략판 — replay 에 불필요, 형식 일관성용) ──
    action_np = np.array(ep_data.column("action").to_pylist(), dtype=np.float32)
    pq.write_table(
        pa.table({
            "episode_index":             pa.array([0],  type=pa.int64()),
            "tasks":                     pa.array([[f"{{'Gesture': '{args.gesture}'}}"  ]]),
            "length":                    pa.array([n],  type=pa.int64()),
            "data/chunk_index":          pa.array([0],  type=pa.int64()),
            "data/file_index":           pa.array([0],  type=pa.int64()),
            "dataset_from_index":        pa.array([0],  type=pa.int64()),
            "dataset_to_index":          pa.array([n],  type=pa.int64()),
            "meta/episodes/chunk_index": pa.array([0],  type=pa.int64()),
            "meta/episodes/file_index":  pa.array([0],  type=pa.int64()),
        }),
        gesture_dir / "meta" / "episodes" / "chunk-000" / "file-000.parquet",
    )

    # ── 11. meta/stats.json (간략판) ──────────────────────────────────────────
    (gesture_dir / "meta" / "stats.json").write_text(json.dumps({
        "action": {
            "min":  action_np.min(axis=0).tolist(),
            "max":  action_np.max(axis=0).tolist(),
            "mean": action_np.mean(axis=0).tolist(),
            "std":  action_np.std(axis=0).tolist(),
        }
    }, indent=4))

    # ── 완료 ──────────────────────────────────────────────────────────────────
    print(f"\n[fetch] 완료: {gesture_dir}")
    print(f"  frames={n}  fps={fps}  episode_src={ep_idx}")
    print(f"\n재생 (왼팔):")
    print(f"  FOLLOWER_PORT=/dev/so_arm_left FOLLOWER_ID=leftarm_test_follower \\")
    print(f"  bash ~/Hylion/jetson/arm/gestures/play_gesture.sh {args.gesture}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
