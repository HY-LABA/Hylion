"""smolvla 사전학습 모델 forward baseline 검증.

03_smolvla_test_on_orin TODO-03 의 책임 — 사전학습 분포에 미러링된 입력으로
1회 forward 가 정상 동작하는지 확인. 카메라 키 / state dim 등은
model.config.input_features 에서 자동 추출하여 사전학습 분포와 일치 보장.

기본 동작 검증만 수행 — latency / VRAM 정량 측정은 measure_latency.py 가 책임.

사용법:
    # HF Hub 기본 모델 (smolvla_base)
    python orin/tests/inference_baseline.py

    # 로컬 ckpt (T3 sync 결과 등)
    python orin/tests/inference_baseline.py \\
        --ckpt-path ~/smolvla/orin/checkpoints/07_pilot_2k/002000

    # HF Hub 특정 repo
    python orin/tests/inference_baseline.py --model-id lerobot/smolvla_base

인자 우선순위: --ckpt-path > --model-id > 기본값 (lerobot/smolvla_base)
--ckpt-path 와 --model-id 는 동시 지정 불가.

레퍼런스:
    - lerobot/utils/hub.py: from_pretrained(pretrained_name_or_path: str | Path)
      로컬 디렉터리 경로 또는 HF repo_id 모두 지원 (line 88~127)
    - lerobot/policies/utils.py: prepare_observation_for_inference (line 97~137)
    - lerobot/policies/factory.py: make_pre_post_processors (line 241~303)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

from lerobot.policies.smolvla import SmolVLAPolicy
from lerobot.policies import make_pre_post_processors
from lerobot.policies.utils import prepare_observation_for_inference

DEFAULT_MODEL_ID = "lerobot/smolvla_base"
TASK = "Pick up the cube and place it in the box."
ROBOT_TYPE = "so101_follower"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SmolVLA forward baseline — ckpt 로드 + 더미 obs forward 검증."
    )
    parser.add_argument(
        "--ckpt-path",
        type=str,
        default=None,
        help=(
            "로컬 pretrained_model 디렉터리 경로 "
            "(예: ~/smolvla/orin/checkpoints/07_pilot_2k/002000). "
            "미지정 시 --model-id 또는 기본 HF Hub 모델을 사용. "
            "--model-id 와 동시 지정 불가."
        ),
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=None,
        help=(
            "HuggingFace Hub repo_id (예: lerobot/smolvla_base). "
            "미지정 시 기본값 lerobot/smolvla_base 사용. "
            "--ckpt-path 와 동시 지정 불가."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # --ckpt-path / --model-id 충돌 검사
    if args.ckpt_path is not None and args.model_id is not None:
        print(
            "[error] --ckpt-path 와 --model-id 는 동시에 지정할 수 없습니다.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 실제 사용 모델 경로 결정
    # 우선순위: --ckpt-path > --model-id > 기본값 (lerobot/smolvla_base)
    if args.ckpt_path is not None:
        effective_model: str | Path = Path(args.ckpt_path).expanduser()
        print(f"[load] 로컬 ckpt 경로: {effective_model}")
    elif args.model_id is not None:
        effective_model = args.model_id
        print(f"[load] HF Hub 모델: {effective_model}")
    else:
        effective_model = DEFAULT_MODEL_ID
        print(f"[load] 기본값: {effective_model}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[device] {device}")

    # 1. 모델 로드
    # from_pretrained: 로컬 디렉터리 경로 또는 HF repo_id 모두 지원
    # 레퍼런스: docs/reference/lerobot/src/lerobot/utils/hub.py L88~127
    print("[load] SmolVLAPolicy.from_pretrained 시작...")
    policy = SmolVLAPolicy.from_pretrained(effective_model).to(device)
    policy.eval()
    print("[load] 완료")

    # 2. input_features 출력 (카메라 키·state dim 자동 확인)
    print("[input_features]")
    for k, v in policy.config.input_features.items():
        print(f"  {k}: {v}")

    # 3. 더미 obs 구성 — input_features 에서 자동 추출 (사전학습 분포 일치)
    dummy_obs: dict[str, np.ndarray] = {}
    for key, feat in policy.config.input_features.items():
        if "image" in key:
            dummy_obs[key] = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        else:
            dim = len(feat.names) if hasattr(feat, "names") and feat.names else 6
            dummy_obs[key] = np.random.rand(dim).astype(np.float32)

    print(f"[dummy_obs keys] {list(dummy_obs.keys())}")

    # 4. 전처리
    # make_pre_post_processors: pretrained_path 는 str | None
    # 로컬 경로는 str 로 변환하여 전달
    # 레퍼런스: docs/reference/lerobot/src/lerobot/policies/factory.py L241~303
    pretrained_path_str: str | None = (
        str(effective_model) if isinstance(effective_model, Path) else effective_model
    )
    preprocess, postprocess = make_pre_post_processors(
        policy.config,
        pretrained_path=pretrained_path_str,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    # 5. obs 텐서 변환
    # prepare_observation_for_inference: (H,W,C) uint8 → (C,H,W) float32/255
    # 레퍼런스: docs/reference/lerobot/src/lerobot/policies/utils.py L97~137
    obs_tensor = prepare_observation_for_inference(
        dummy_obs, device=device, task=TASK, robot_type=ROBOT_TYPE
    )
    obs_tensor = preprocess(obs_tensor)

    # 6. forward
    with torch.inference_mode():
        action = policy.select_action(obs_tensor)

    action = postprocess(action)

    # 7. 결과 출력
    print(f"[result] Action shape: {tuple(action.shape)}")
    print(f"[result] Action dtype: {action.dtype}")
    print(f"[result] Action min:   {action.min().item():.6f}")
    print(f"[result] Action max:   {action.max().item():.6f}")

    # DOD 검증: action shape (1, 6)
    if action.shape == (1, 6):
        print("[DOD] action shape (1, 6) OK")
    else:
        print(
            f"[DOD] action shape 예상 (1, 6), 실제 {tuple(action.shape)} "
            "— 카메라 키·state dim 확인 필요",
            file=sys.stderr,
        )

    print("[done] exit 0")


if __name__ == "__main__":
    main()
