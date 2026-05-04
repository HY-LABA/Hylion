"""interactive_cli flow 3·4·5 — ckpt 선택 + hil_inference 실행 + 시연 데모 결과.

사용자 결정 (A) 3단계 순차 (awaits_user-B 답 2026-05-02):
  flow 3: ckpt 선택 — 3개 소스 메뉴
            (1) HF Hub repo_id 입력
            (2) 로컬 ckpt 경로 직접 입력
            (3) 기본값 smolvla_base 고정 (추가 입력 없음)
            ※ orin/checkpoints/ 자동 탐색은 미채택 (사용자 합의 X)
  flow 4: hil_inference.py 실행
            --gate-json orin/config/ 자동 전달
            ckpt 소스에 따라 --model-id / --ckpt-path 인자 자동 추가
  flow 5: 시연 데모 결과
            "로봇이 움직이고 있습니다" + Ctrl+C 안내
            hil_inference 종료 후 결과 요약 출력

설계 기반:
  - 13_orin_cli_flow.md §3·§4·§5 패턴 그대로 적용
  - hil_inference.py argparse 인자 (line 183~245): --mode, --gate-json, --output-json,
    --max-steps, --n-action-steps (직접 Read 확인)
  - hil_inference.py 에 O2 에서 추가할 --model-id / --ckpt-path 인자를 활용
  - dry-run 기본 제안, live 는 사용자 명시 선택

주의: flow 2 (env_check.py) 통과 이후에만 호출되어야 한다.
"""

import subprocess
import sys
from pathlib import Path

# 기본 model ID (hil_inference.py line 48 에서 동기화)
DEFAULT_MODEL_ID = "lerobot/smolvla_base"

# dry-run 기본 출력 JSON 경로
DEFAULT_DRYRUN_JSON = "/tmp/hil_dryrun.json"

# hil_inference.py 의 기본 max-steps
DEFAULT_MAX_STEPS = 100


def flow3_select_ckpt() -> tuple[str, str | None, str | None]:
    """flow 3: ckpt 선택 메뉴.

    사용자 결정 — 3개 소스 (awaits_user-B, 2026-05-02):
      1. HF Hub repo_id 입력
      2. 로컬 ckpt 경로 직접 입력
      3. 기본값 smolvla_base 사용 (추가 입력 없음)

    Returns:
        (source_label, model_id, ckpt_path)
          source_label: "hub" | "local" | "default"
          model_id: HF Hub repo_id (소스 1일 때) 또는 None
          ckpt_path: 로컬 경로 문자열 (소스 2일 때) 또는 None
    """
    print()
    print("=" * 60)
    print(" flow 3 — ckpt 선택")
    print("=" * 60)
    print()
    print("사용할 모델 checkpoint 소스를 선택하세요:")
    print()
    print("  1. HF Hub repo_id 입력  (예: lerobot/smolvla_base, <username>/<repo>)")
    print("  2. 로컬 ckpt 경로 직접 입력")
    print(f"  3. 기본값 사용  ({DEFAULT_MODEL_ID})")
    print()

    while True:
        try:
            raw = input("번호 선택 [1~3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[취소] ckpt 선택을 취소합니다.")
            sys.exit(0)

        if raw == "1":
            return _flow3_hub_input()
        elif raw == "2":
            return _flow3_local_input()
        elif raw == "3":
            print(f"\n[선택] 기본값 사용: {DEFAULT_MODEL_ID}")
            return "default", None, None
        else:
            print("  1, 2, 3 중 하나를 입력하세요.")


def _flow3_hub_input() -> tuple[str, str | None, str | None]:
    """소스 1: HF Hub repo_id 입력."""
    print()
    print("  HF Hub repo_id 를 입력하세요.")
    print("  (예: lerobot/smolvla_base, <username>/<repo>)")
    print(f"  빈 줄 입력 시 기본값 사용 ({DEFAULT_MODEL_ID})")
    print()

    try:
        raw = input("  repo_id: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[취소] ckpt 선택을 취소합니다.")
        sys.exit(0)

    if not raw:
        print(f"  [기본값] {DEFAULT_MODEL_ID}")
        return "default", None, None

    print(f"\n[선택] HF Hub: {raw}")
    return "hub", raw, None


def _flow3_local_input() -> tuple[str, str | None, str | None]:
    """소스 2: 로컬 ckpt 경로 직접 입력."""
    print()
    print("  로컬 ckpt pretrained_model 경로를 입력하세요.")
    print("  예: ~/smolvla/orin/checkpoints/<run>/<step>/pretrained_model")
    print()

    try:
        raw = input("  경로: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        print("[취소] ckpt 선택을 취소합니다.")
        sys.exit(0)

    if not raw:
        print("  경로를 입력하지 않았습니다. 기본값을 사용합니다.")
        return "default", None, None

    # 경로 확장 (~, 환경변수)
    expanded = str(Path(raw).expanduser())
    ckpt_path = Path(expanded)

    if not ckpt_path.exists():
        print(f"  [경고] 경로가 존재하지 않습니다: {expanded}")
        print("         그대로 진행하시겠습니까? (존재하지 않는 경로는 hil_inference 에서 오류)")
        try:
            confirm = input("  [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if confirm not in ("", "y", "yes"):
            print("  ckpt 선택으로 돌아갑니다.")
            return flow3_select_ckpt()

    print(f"\n[선택] 로컬 경로: {expanded}")
    return "local", None, expanded


def _flow4_ask_mode() -> str:
    """flow 4 전처리: dry-run 또는 live 선택."""
    print()
    print("실행 모드를 선택하세요:")
    print("  1. dry-run  (SO-ARM 미구동 — action 로그만 출력, 기본값)")
    print("  2. live     (SO-ARM 실제 구동 — 안전 주의)")
    print()

    while True:
        try:
            raw = input("번호 선택 [1~2, 기본 1]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if raw in ("", "1"):
            print("[모드] dry-run")
            return "dry-run"
        elif raw == "2":
            print()
            print("[주의] live 모드: SO-ARM follower 가 실제로 움직입니다.")
            print("       로봇과 주변 물체를 안전한 위치에 배치하세요.")
            try:
                confirm = input("계속 진행하시겠습니까? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if confirm in ("", "y", "yes"):
                print("[모드] live")
                return "live"
            else:
                print("  dry-run 으로 선택합니다.")
                return "dry-run"
        else:
            print("  1 또는 2 를 입력하세요.")


def flow4_run_inference(
    script_dir: Path,
    source_label: str,
    model_id: str | None,
    ckpt_path: str | None,
    mode: str,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> int:
    """flow 4: hil_inference.py subprocess 실행.

    13_orin_cli_flow.md §4 run_inference() 패턴 적용:
      - --gate-json orin/config/ 자동 전달 (ports.json + cameras.json 자동 채움)
      - ckpt 소스에 따라 --model-id / --ckpt-path 인자 추가
      - dry-run 시 --output-json /tmp/hil_dryrun.json 자동 추가

    hil_inference.py 경로: script_dir.parent.parent / "inference" / "hil_inference.py"
    config 경로: script_dir.parent.parent / "config"

    Returns:
        subprocess returncode (0 = 정상, 비0 = 오류 또는 Ctrl+C)
    """
    hil_script = script_dir.parent.parent / "inference" / "hil_inference.py"
    config_dir = script_dir.parent.parent / "config"

    if not hil_script.exists():
        print(f"[ERROR] hil_inference.py 미존재: {hil_script}", file=sys.stderr)
        return 1

    cmd = [
        sys.executable, str(hil_script),
        "--gate-json", str(config_dir),
        "--mode", mode,
        "--max-steps", str(max_steps),
    ]

    # ckpt 인자: source 에 따라 --model-id / --ckpt-path 추가
    # (hil_inference.py 에 O2 에서 추가된 인자 활용)
    if source_label == "hub" and model_id is not None:
        cmd += ["--model-id", model_id]
    elif source_label == "local" and ckpt_path is not None:
        cmd += ["--ckpt-path", ckpt_path]
    # source_label == "default" 이면 추가 인자 없음 (hil_inference.py 기본값 사용)

    # dry-run 은 --output-json 필수 (hil_inference.py line 257~259)
    if mode == "dry-run":
        cmd += ["--output-json", DEFAULT_DRYRUN_JSON]

    print()
    print("=" * 60)
    print(" flow 4 — hil_inference 실행")
    print("=" * 60)
    print()

    if mode == "live":
        print("[flow 4] 로봇이 움직이고 있습니다.")
        print("         관찰 후 Ctrl+C 로 종료하세요.")
    else:
        print("[flow 4] dry-run 중 (SO-ARM 미구동). action 로그를 확인하세요.")

    print()
    print(f"  실행 명령: {' '.join(str(c) for c in cmd)}")
    print()

    result = subprocess.run(cmd, check=False)
    return result.returncode


def flow5_show_result(
    returncode: int,
    mode: str,
    source_label: str,
    model_id: str | None,
    ckpt_path: str | None,
) -> None:
    """flow 5: 시연 데모 결과 출력.

    13_orin_cli_flow.md §5 포함 시 패턴 적용:
      - hil_inference 종료 후 결과 요약
      - dry-run 이면 output JSON 경로 안내
      - 종료 코드 분기 (정상/Ctrl+C/오류)
    """
    print()
    print("=" * 60)
    print(" flow 5 — 추론 결과")
    print("=" * 60)
    print()

    # ckpt 정보 표시
    if source_label == "hub" and model_id:
        print(f"  사용 모델: {model_id} (HF Hub)")
    elif source_label == "local" and ckpt_path:
        print(f"  사용 모델: {ckpt_path} (로컬)")
    else:
        print(f"  사용 모델: {DEFAULT_MODEL_ID} (기본값)")

    print(f"  실행 모드: {mode}")

    if returncode == 0:
        print("  상태: 정상 완료 (max-steps 도달 또는 Ctrl+C)")
    elif returncode == 130:
        # SIGINT (Ctrl+C) — subprocess 에서 130 으로 전달되는 경우
        print("  상태: Ctrl+C 로 종료")
    else:
        print(f"  상태: 비정상 종료 (exit {returncode})")
        print("         hil_inference.py 로그를 확인하세요.")

    if mode == "dry-run":
        print(f"  결과 JSON: {DEFAULT_DRYRUN_JSON}")
        print("  (정성 관찰: action 값이 모든 step 에서 유효한지 확인)")

    print()


def run_inference_flow(script_dir: Path) -> int:
    """flow 3·4·5 순차 실행 진입점.

    entry.py 에서 orin 분기 시 호출.

    Returns:
        종료 코드 (0 = 정상, 1 = 오류)
    """
    # flow 3: ckpt 선택
    source_label, model_id, ckpt_path = flow3_select_ckpt()

    # flow 4 전처리: 모드 선택
    mode = _flow4_ask_mode()

    # flow 4: hil_inference 실행
    returncode = flow4_run_inference(
        script_dir=script_dir,
        source_label=source_label,
        model_id=model_id,
        ckpt_path=ckpt_path,
        mode=mode,
    )

    # flow 5: 결과 보고
    flow5_show_result(
        returncode=returncode,
        mode=mode,
        source_label=source_label,
        model_id=model_id,
        ckpt_path=ckpt_path,
    )

    # returncode 0 (정상) 또는 130 (Ctrl+C) 모두 정상 종료로 취급
    return 0 if returncode in (0, 130) else 1
