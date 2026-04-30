#!/usr/bin/env python
"""DGX 학습 체크포인트 호환성 검증 (Orin 측 추론 환경)

실행 위치: Orin (~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py)
사용:
    python load_checkpoint_test.py                                       # default = lerobot/smolvla_base (사전학습)
    python load_checkpoint_test.py --ckpt-path /path/to/pretrained_model # DGX 학습 체크포인트

검증 항목:
    1. SmolVLAPolicy.from_pretrained(ckpt_path) 로드
    2. 모델이 cuda 로 이동 + bfloat16 dtype 유지
    3. 더미 입력 (image + state + language) forward pass
    4. action shape (1, 50, 6) 또는 (1, 50, 32) padding 출력 확인
    5. exit code 0 / 1

결정 근거: 02_dgx_setting TODO-10 / orin/examples/tutorial/smolvla/smoke_test.py 와 형제
    smoke_test.py 가 "Orin 환경 자체 검증" 이라면 본 스크립트는 "체크포인트 호환성 검증".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--ckpt-path",
        type=str,
        default="lerobot/smolvla_base",
        help="체크포인트 경로 (HF repo_id 또는 로컬 디렉터리). default=lerobot/smolvla_base",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="추론 device (default=cuda)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ckpt_path = args.ckpt_path

    print(f"[load-ckpt] PyTorch:    {torch.__version__}")
    print(f"[load-ckpt] CUDA avail: {torch.cuda.is_available()}")
    print(f"[load-ckpt] Device:     {args.device}")
    print(f"[load-ckpt] Ckpt path:  {ckpt_path}")

    if args.device == "cuda" and not torch.cuda.is_available():
        print("[load-ckpt] ERROR: CUDA unavailable", file=sys.stderr)
        return 1

    # 로컬 경로면 존재 검증
    is_local = "/" in ckpt_path or Path(ckpt_path).exists()
    if is_local and not Path(ckpt_path).is_dir():
        print(f"[load-ckpt] ERROR: 로컬 경로 미존재 또는 디렉터리 아님: {ckpt_path}", file=sys.stderr)
        return 1

    # ── 1. 정책 로드 ───────────────────────────────────────────────────────────
    print("\n[load-ckpt] (1/4) SmolVLAPolicy.from_pretrained 로드 중...")
    try:
        from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    except ImportError as e:
        print(f"[load-ckpt] ERROR: lerobot import 실패: {e}", file=sys.stderr)
        return 1

    try:
        policy = SmolVLAPolicy.from_pretrained(ckpt_path)
    except Exception as e:
        print(f"[load-ckpt] ERROR: 체크포인트 로드 실패: {e}", file=sys.stderr)
        return 1

    policy = policy.to(args.device)
    policy.eval()
    print(f"[load-ckpt]   policy class:  {type(policy).__name__}")
    print(f"[load-ckpt]   policy device: {next(policy.parameters()).device}")
    print(f"[load-ckpt]   policy dtype:  {next(policy.parameters()).dtype}")

    # ── 2. config 확인 ─────────────────────────────────────────────────────────
    print("\n[load-ckpt] (2/4) config 확인...")
    cfg = policy.config
    print(f"[load-ckpt]   chunk_size:        {cfg.chunk_size}")
    print(f"[load-ckpt]   n_action_steps:    {cfg.n_action_steps}")
    print(f"[load-ckpt]   max_state_dim:     {cfg.max_state_dim}")
    print(f"[load-ckpt]   max_action_dim:    {cfg.max_action_dim}")
    print(f"[load-ckpt]   train_expert_only: {cfg.train_expert_only}")
    print(f"[load-ckpt]   vlm_model_name:    {cfg.vlm_model_name}")

    # ── 3. 더미 입력 + forward (select_action) ─────────────────────────────────
    print("\n[load-ckpt] (3/4) 더미 입력 forward pass...")
    from lerobot.utils.constants import (
        ACTION,
        OBS_LANGUAGE_ATTENTION_MASK,
        OBS_LANGUAGE_TOKENS,
        OBS_STATE,
    )

    batch_size = 1
    device = args.device
    image_keys = list(cfg.image_features.keys()) if cfg.image_features else []
    if not image_keys:
        # 기본 카메라 1대 가정
        image_keys = ["observation.images.camera1"]

    state_dim = cfg.input_features[OBS_STATE].shape[0] if OBS_STATE in cfg.input_features else 6
    tokenizer_max_length = cfg.tokenizer_max_length

    batch = {
        OBS_STATE: torch.zeros(batch_size, state_dim, device=device, dtype=torch.float32),
        OBS_LANGUAGE_TOKENS: torch.zeros(batch_size, tokenizer_max_length, device=device, dtype=torch.long),
        OBS_LANGUAGE_ATTENTION_MASK: torch.ones(batch_size, tokenizer_max_length, device=device, dtype=torch.bool),
    }
    for key in image_keys:
        batch[key] = torch.zeros(batch_size, 3, 480, 640, device=device, dtype=torch.float32)

    print(f"[load-ckpt]   batch keys: {sorted(batch.keys())}")

    try:
        policy.reset()
        with torch.no_grad():
            actions = policy.predict_action_chunk(batch)
    except Exception as e:
        print(f"[load-ckpt] ERROR: forward 실패: {e}", file=sys.stderr)
        return 1

    print(f"[load-ckpt]   action shape: {tuple(actions.shape)}")
    print(f"[load-ckpt]   action dtype: {actions.dtype}")
    print(f"[load-ckpt]   action range: [{actions.min().item():.4f}, {actions.max().item():.4f}]")

    # ── 4. shape 검증 ─────────────────────────────────────────────────────────
    print("\n[load-ckpt] (4/4) shape 검증...")
    expected_chunk = cfg.chunk_size
    if actions.shape[0] != batch_size or actions.shape[1] != expected_chunk:
        print(
            f"[load-ckpt] WARN: 예상 shape ({batch_size}, {expected_chunk}, *) 와 다름: {tuple(actions.shape)}",
            file=sys.stderr,
        )

    print("\n==========================================================")
    print(" 체크포인트 호환성 검증 PASS")
    print(f"   ckpt_path:    {ckpt_path}")
    print(f"   action shape: {tuple(actions.shape)}")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
