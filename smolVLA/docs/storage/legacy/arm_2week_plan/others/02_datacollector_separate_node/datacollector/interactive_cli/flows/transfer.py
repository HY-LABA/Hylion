"""interactive_cli flow 7 — 전송 방식 선택.

3분기 메뉴:
  (1) HF Hub 업로드  — push_dataset_hub.sh 직접 호출 (datacollector 머신에서 실행 가능)
  (2) rsync → DGX   — sync_dataset_collector_to_dgx.sh 는 devPC 전용 → 안내 메시지만
  (3) 안함          — 로컬 저장 (datacollector/data/<dataset>/) 만 유지

레퍼런스 직접 인용:

[1] push_dataset_hub.sh pre-check (line 104~117):
    HF_TOKEN 환경변수 또는 huggingface-cli 로그인 확인
    HF_AUTH_OK: "token" / "cached" / "false"

[2] push_dataset_hub.sh 인자 형식 (line 6~14):
    bash push_dataset_hub.sh \\
        --dataset ~/smolvla/datacollector/data/<name> \\
        --repo-id <HF_USER>/<REPO_NAME>
    [--private]

[3] sync_dataset_collector_to_dgx.sh line 6:
    "실행 위치: devPC (어디서든)"
    → datacollector 직접 호출 금지, 안내 메시지로 대체

[4] sync_dataset_collector_to_dgx.sh SSH alias 필요 (line 67~77):
    ~/.ssh/config 에 'Host datacollector' + 'Host dgx' 등록

[5] D1 §5 transfer.py 통합 흐름 코드 개요 그대로 적용.
"""

import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# HF Token 확인 (push_dataset_hub.sh line 104~117 패턴 미러)
# ---------------------------------------------------------------------------

def _check_hf_token() -> tuple[bool, str]:
    """HF 인증 정보 유무 확인.

    push_dataset_hub.sh line 104~117 패턴 미러:
      HF_TOKEN 환경변수 우선 → huggingface-cli cached token 확인.

    Returns:
        (ok, auth_type): auth_type in {"token", "cached", "none"}
    """
    hf_token = os.environ.get("HF_TOKEN", "")
    if hf_token:
        return True, "token"

    try:
        result = subprocess.run(
            ["python3", "-c",
             "from huggingface_hub import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)"],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return True, "cached"
    except FileNotFoundError:
        pass

    return False, "none"


# ---------------------------------------------------------------------------
# 분기 1 — HF Hub 업로드 (D1 §5 transfer_to_hub 패턴 그대로)
# ---------------------------------------------------------------------------

def _transfer_to_hub(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
    private: bool = False,
) -> int:
    """push_dataset_hub.sh 직접 호출.

    D1 §5 transfer_to_hub 패턴:
      push_script = script_dir.parent.parent / "scripts" / "push_dataset_hub.sh"
      cmd = ["bash", str(push_script), "--dataset", local_dataset_path, "--repo-id", repo_id]

    Args:
        script_dir: flows/ 디렉터리 경로
        local_dataset_path: 로컬 dataset 경로
        repo_id: HF Hub repo ID
        private: private repo 여부

    Returns:
        subprocess returncode
    """
    push_script = script_dir.parent.parent / "scripts" / "push_dataset_hub.sh"

    if not push_script.exists():
        print(f"[flow 7] ERROR: push_dataset_hub.sh 미발견: {push_script}", file=sys.stderr)
        return 1

    cmd = [
        "bash", str(push_script),
        "--dataset", local_dataset_path,
        "--repo-id", repo_id,
    ]
    if private:
        cmd.append("--private")

    result = subprocess.run(cmd, check=False)
    return result.returncode


# ---------------------------------------------------------------------------
# 분기 2 — rsync DGX 안내 (D1 §5 guide_rsync_to_dgx 패턴 그대로)
# ---------------------------------------------------------------------------

def _guide_rsync_to_dgx(repo_id: str) -> None:
    """rsync DGX 전송 안내 (직접 실행 X).

    sync_dataset_collector_to_dgx.sh 는 devPC 에서 실행해야 함 (line 6).
    datacollector 터미널에서 직접 호출 금지 → 안내 메시지로 대체.

    D1 §5 guide_rsync_to_dgx 패턴 그대로.
    """
    dataset_name = repo_id.split("/")[-1]
    print()
    print("[flow 7] rsync DGX 전송 안내")
    print("  sync_dataset_collector_to_dgx.sh 는 devPC 에서 실행해야 합니다.")
    print()
    print("  devPC 터미널에서 아래 명령을 실행하세요:")
    print(f"    bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset {dataset_name}")
    print()
    print("  필요 조건: ~/.ssh/config 에 'Host datacollector' + 'Host dgx' 등록")
    print("  (docs/storage/09_datacollector_setup.md §5-1 참조)")


# ---------------------------------------------------------------------------
# 분기 3 — 로컬 저장 유지 (D1 §5 keep_local 패턴 그대로)
# ---------------------------------------------------------------------------

def _keep_local(local_dataset_path: str, repo_id: str) -> None:
    """로컬 저장 유지 안내.

    D1 §5 keep_local 패턴 그대로.
    """
    print()
    print(f"[flow 7] 로컬 저장 유지: {local_dataset_path}")
    print("  나중에 전송하려면:")
    print(
        f"  HF Hub:  bash datacollector/scripts/push_dataset_hub.sh"
        f" --dataset {local_dataset_path} --repo-id {repo_id}"
    )
    dataset_name = repo_id.split("/")[-1]
    print(
        f"  rsync:   (devPC 에서)"
        f" bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset {dataset_name}"
    )


# ---------------------------------------------------------------------------
# flow 7 메인 함수 (D1 §5 flow7_select_transfer 패턴 그대로)
# ---------------------------------------------------------------------------

def flow7_select_transfer(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
) -> None:
    """flow 7: 전송 방식 선택.

    spec line 60~63:
      "[저장경로]에 저장되었습니다" 출력 + 전송 방식 사용자 선택

    D1 §5 flow7_select_transfer 패턴 그대로.

    Args:
        script_dir: flows/ 디렉터리 경로
        local_dataset_path: lerobot-record 가 저장한 로컬 경로
        repo_id: HF Hub repo ID (flow 6 에서 입력받은 값)
    """
    print()
    print("=" * 60)
    print(" flow 7 — 전송 방식 선택")
    print("=" * 60)
    print()
    print(f"데이터셋이 저장되었습니다: {local_dataset_path}")
    print()
    print("전송 방식을 선택해주세요:")
    print("  (1) HF Hub 업로드 (인터넷 필요)")
    print("  (2) rsync → DGX (devPC 에서 실행 안내)")
    print("  (3) 안함 (로컬 저장 유지)")
    print()

    while True:
        try:
            raw = input("번호 선택 [1~3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 7] 종료됩니다. 로컬 저장 유지.")
            _keep_local(local_dataset_path, repo_id)
            return

        if raw == "1":
            # HF Hub 업로드 — 토큰 확인 먼저
            token_ok, auth_type = _check_hf_token()
            if not token_ok:
                print()
                print("[flow 7] HuggingFace 인증 정보 없음.")
                print("  옵션 A (권장): export HF_TOKEN=hf_xxxxxxxxxx")
                print("  옵션 B: huggingface-cli login")
                print()
                print("인증 설정 후 다시 선택하세요. (또는 다른 옵션 선택)")
                continue

            print(f"[flow 7] HF 인증 확인 ({auth_type})")
            try:
                private_input = input("private repo 로 업로드? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                private_input = "n"

            private = private_input in ("y", "yes")

            returncode = _transfer_to_hub(
                script_dir, local_dataset_path, repo_id, private
            )
            if returncode == 0:
                print(f"[flow 7] HF Hub 업로드 완료: https://huggingface.co/datasets/{repo_id}")
            else:
                print(f"[flow 7] HF Hub 업로드 실패 (returncode={returncode}). 나중에 재시도 안내:")
                print(
                    f"  bash datacollector/scripts/push_dataset_hub.sh"
                    f" --dataset {local_dataset_path} --repo-id {repo_id}"
                )
            return

        elif raw == "2":
            _guide_rsync_to_dgx(repo_id)
            return

        elif raw == "3":
            _keep_local(local_dataset_path, repo_id)
            return

        else:
            print("  1, 2, 3 중 하나를 입력하세요.")
