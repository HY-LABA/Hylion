"""interactive_cli flow 3·4·5 — DGX 학습 (시나리오 선택·데이터셋·학습 + ckpt 관리).

옵션 C 3단계 구조 (사용자 결정 2026-05-02):
  flow 3: preflight 재확인 + 시나리오 선택 (smoke/s1/s3/lora)
  flow 4: 데이터셋 선택 (HF Hub repo_id / 로컬 dgx/datasets/ / 기본값)
  flow 5: 학습 실행 + ckpt 관리 통합
           smoke: smoke_test.sh subprocess 호출 (동의 게이트 포함)
           실 학습: lerobot-train draccus 인자 동적 생성
           ckpt 전송: 케이스 목록 출력 + 사용자 선택

설계 기반:
  - 14_dgx_cli_flow.md §2~§5 (X1 산출물)
  - dgx/scripts/smoke_test.sh — 직접 Read (line 44~45, 68~81)
  - dgx/scripts/save_dummy_checkpoint.sh — 직접 Read (line 25, 62~63)

"""

import subprocess
import sys
from pathlib import Path

from flows._back import is_back


# ---------------------------------------------------------------------------
# 시나리오 메타데이터
#   preflight_check.sh line 23~35 에서 인용한 메모리 요구치
# ---------------------------------------------------------------------------
SCENARIOS = {
    "smoke": {
        "label": "Smoke test (1 step, ~100MB 다운로드 가능)",
        "memory_gb": 20,
        "description": "lerobot-train --steps=1, 환경 검증 전용",
    },
    "s1": {
        "label": "S1 — 04 / 06 1차 학습 (35 GB)",
        "memory_gb": 35,
        "description": "실 학습: 1차 fine-tuning",
    },
    "s3": {
        "label": "S3 — 06 2차 학습 (VLM 풀 학습, 65 GB)",
        "memory_gb": 65,
        "description": "실 학습: VLM 포함 풀 fine-tuning",
    },
    "lora": {
        "label": "LoRA fallback (28 GB)",
        "memory_gb": 28,
        "description": "실 학습: LoRA fine-tuning",
    },
}

SMOKE_DEFAULT_DATASET = "lerobot/svla_so100_pickplace"
DEFAULT_POLICY_PATH = "lerobot/smolvla_base"

# ckpt 케이스 안내
CKPT_CASES = {
    "1": {
        "label": "케이스 1·2 — Orin 과 동일 네트워크 / devPC 2-hop",
        "guide": (
            "devPC 에서 실행:\n"
            "  bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh --run <run_name>\n"
            "\n"
            "  (케이스 1: devPC·DGX·Orin 동일 광역 네트워크)\n"
            "  (케이스 2: Orin 인터넷 가능, 다른 서브넷 → devPC 2-hop)\n"
        ),
    },
    "2": {
        "label": "케이스 3 — 시연장 Orin 인터넷 격리 (ckpt sync 신규 예정)",
        "guide": (
            "[안내] DataCollector 노드가 06 결정으로 운영 종료됨.\n"
            "  DGX → DataCollector 우회 경로는 현재 무효입니다.\n"
            "\n"
            "  DGX → Orin 직접 ckpt sync 스크립트는 차기 사이클 (07_leftarmVLA) 에서 신규 작성 예정.\n"
            "  현재는 케이스 1·2 (동일 네트워크 또는 devPC 2-hop) 또는 케이스 4 (USB) 를 사용하세요.\n"
        ),
    },
    "3": {
        "label": "나중에 직접 전송 (안내만)",
        "guide": (
            "전송 방법:\n"
            "  docs/storage/others/ckpt_transfer_scenarios.md 에서\n"
            "  케이스 1·2·4 중 해당하는 절차를 따르세요.\n"
            "  (케이스 3 DataCollector 우회는 06 결정으로 무효 — 차기 사이클 신규 예정)\n"
        ),
    },
    "4": {
        "label": "케이스 4 — USB 드라이브 전송",
        "guide": (
            "USB 드라이브 절차:\n"
            "  docs/storage/others/ckpt_transfer_scenarios.md §4 를 따르세요.\n"
        ),
    },
}


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------

def _prompt(message: str) -> str:
    """input() 래퍼 — EOFError·KeyboardInterrupt 보호."""
    try:
        return input(message).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise KeyboardInterrupt


def _yn_prompt(message: str, default_yes: bool = True) -> bool:
    """Y/n 또는 y/N 프롬프트.

    Returns:
        True: 사용자 동의 / False: 거부 또는 인터럽트
    """
    hint = "[Y/n]" if default_yes else "[y/N]"
    try:
        answer = _prompt(f"{message} {hint} ")
    except KeyboardInterrupt:
        return False

    if answer == "":
        return default_yes
    return answer.lower() in ("y", "yes")


# ---------------------------------------------------------------------------
# flow 3 — preflight 재확인 + 시나리오 선택
# ---------------------------------------------------------------------------

def flow3_select_scenario(script_dir: Path) -> str | None:
    """flow 3: preflight 재확인 + 시나리오 선택.

    14_dgx_cli_flow.md §2-4 옵션 C:
      "flow 3: preflight 재확인 + 시나리오 선택 (smoke/s1/s3/lora)"

    smoke 선택 시 동의 게이트 없음 (flow 5 에서 처리).

    Returns:
        시나리오 키 ("smoke"|"s1"|"s3"|"lora") 또는 None (종료)
    """
    print()
    print("=" * 60)
    print(" flow 3 — 학습 시나리오 선택")
    print("=" * 60)
    print()
    print("어떤 시나리오로 학습하겠습니까?")
    print()

    scenario_keys = list(SCENARIOS.keys())
    for i, key in enumerate(scenario_keys, start=1):
        s = SCENARIOS[key]
        print(f"  {i}. {s['label']}")
        print(f"     {s['description']}")
        print()

    print(f"  {len(scenario_keys) + 1}. 종료")
    print()

    while True:
        try:
            raw = _prompt(f"번호 선택 [1~{len(scenario_keys) + 1}, b: 뒤로]: ")
        except KeyboardInterrupt:
            return None

        # b/back: mode 선택으로 복귀
        if is_back(raw):
            print()
            print("[flow 3] 뒤로가기 — mode 선택으로 돌아갑니다.")
            return None

        if not raw.isdigit():
            print("  숫자 또는 b(뒤로) 를 입력하세요.")
            continue

        choice = int(raw)

        if choice == len(scenario_keys) + 1:
            print("종료합니다.")
            return None

        if 1 <= choice <= len(scenario_keys):
            selected = scenario_keys[choice - 1]
            print(f"\n[선택] {SCENARIOS[selected]['label']}")
            return selected

        print(f"  유효한 번호를 입력하세요 (1~{len(scenario_keys) + 1}) 또는 b(뒤로).")


# ---------------------------------------------------------------------------
# flow 4 — 데이터셋 선택
# ---------------------------------------------------------------------------

def _list_local_datasets(script_dir: Path) -> list[str]:
    """dgx/datasets/ 하위 디렉터리 목록 반환.

    14_dgx_cli_flow.md §3-1: 로컬 rsync 결과는 ~/smolvla/dgx/datasets/<name>.
    """
    datasets_dir = script_dir.parent / "datasets"
    if not datasets_dir.exists():
        return []
    return [p.name for p in sorted(datasets_dir.iterdir()) if p.is_dir()]


def flow4_select_dataset(script_dir: Path, scenario: str) -> str | None:
    """flow 4: 데이터셋 선택.

    14_dgx_cli_flow.md §3 데이터셋 선택 메커니즘:
      1. HF Hub repo_id 직접 입력
      2. 로컬 ~/smolvla/dgx/datasets/ 에서 선택
      3. 기본 smoke test 데이터셋 사용 (lerobot/svla_so100_pickplace)

    smoke 시나리오는 기본 데이터셋 고정 (smoke_test.sh line 68~69 하드코드).
    실 학습은 3 소스 중 선택.

    Returns:
        데이터셋 repo_id 문자열 또는 None (종료)
    """
    print()
    print("=" * 60)
    print(" flow 4 — 데이터셋 선택")
    print("=" * 60)

    if scenario == "smoke":
        # smoke_test.sh line 68~69: --dataset.repo_id=lerobot/svla_so100_pickplace 하드코드
        print()
        print("  smoke test 는 고정 데이터셋을 사용합니다:")
        print(f"    {SMOKE_DEFAULT_DATASET}")
        print()
        print("  (smoke_test.sh line 68~69 하드코드 — 변경 불가)")
        return SMOKE_DEFAULT_DATASET

    # 실 학습: 3 소스 메뉴
    print()
    print("어떤 데이터셋으로 학습하겠습니까?")
    print()

    local_datasets = _list_local_datasets(script_dir)

    print("  1. HF Hub repo_id 직접 입력")
    print("     예: lerobot/svla_so100_pickplace")

    if local_datasets:
        print(f"  2. 로컬 dgx/datasets/ 에서 선택 ({len(local_datasets)}개 발견)")
    else:
        print("  2. 로컬 dgx/datasets/ 에서 선택 (없음 — rsync 먼저 실행 필요)")

    print(f"  3. 기본 smoke 데이터셋 ({SMOKE_DEFAULT_DATASET})")
    print("  4. 종료")
    print()

    while True:
        try:
            raw = _prompt("번호 선택 [1~4, b: 뒤로]: ")
        except KeyboardInterrupt:
            return None

        # b/back: 시나리오 선택으로 복귀
        if is_back(raw):
            print()
            print("[flow 4] 뒤로가기 — 시나리오 선택으로 돌아갑니다.")
            return None

        if not raw.isdigit():
            print("  숫자 또는 b(뒤로) 를 입력하세요.")
            continue

        choice = int(raw)

        if choice == 4:
            print("종료합니다.")
            return None

        if choice == 1:
            # HF Hub repo_id 직접 입력
            try:
                repo_id = _prompt("HF Hub repo_id 입력 (예: lerobot/svla_so100_pickplace, b: 뒤로): ")
            except KeyboardInterrupt:
                return None
            if is_back(repo_id):
                print()
                print("[flow 4] 뒤로가기.")
                continue
            if not repo_id:
                print("  repo_id 가 비어있습니다. 다시 입력하세요.")
                continue
            print(f"\n[선택] HF Hub: {repo_id}")
            return repo_id

        if choice == 2:
            if not local_datasets:
                print("  로컬 데이터셋이 없습니다. DGX 에서 lerobot-record 로 데이터 수집 후 학습을 진행하세요.")
                continue
            return _select_local_dataset(local_datasets)

        if choice == 3:
            print(f"\n[선택] 기본 데이터셋: {SMOKE_DEFAULT_DATASET}")
            return SMOKE_DEFAULT_DATASET

        print("  유효한 번호를 입력하세요 (1~4) 또는 b(뒤로).")


def _select_local_dataset(local_datasets: list[str]) -> str | None:
    """로컬 데이터셋 선택 서브메뉴."""
    print()
    print("  로컬 데이터셋 목록:")
    for i, name in enumerate(local_datasets, start=1):
        print(f"    {i}. {name}")
    print(f"    {len(local_datasets) + 1}. 돌아가기")
    print()

    while True:
        try:
            raw = _prompt(f"번호 선택 [1~{len(local_datasets) + 1}, b: 뒤로]: ")
        except KeyboardInterrupt:
            return None

        # b/back: 데이터셋 선택 메뉴로 복귀
        if is_back(raw):
            print()
            print("[flow 4] 뒤로가기.")
            return None

        if not raw.isdigit():
            print("  숫자 또는 b(뒤로) 를 입력하세요.")
            continue

        choice = int(raw)
        if choice == len(local_datasets) + 1:
            return None  # 돌아가기

        if 1 <= choice <= len(local_datasets):
            name = local_datasets[choice - 1]
            # 로컬 경로를 repo_id 형식으로 반환 (절대 경로는 lerobot-train 이 처리)
            # 실제로는 로컬 디렉터리 경로를 전달 (~/smolvla/dgx/datasets/<name>)
            local_path = f"~/smolvla/dgx/datasets/{name}"
            print(f"\n[선택] 로컬: {local_path}")
            return local_path

        print(f"  유효한 번호를 입력하세요 (1~{len(local_datasets) + 1}) 또는 b(뒤로).")


# ---------------------------------------------------------------------------
# flow 5 — 학습 실행 + ckpt 관리
# ---------------------------------------------------------------------------

def _smoke_consent_gate() -> bool:
    """smoke test 동의 게이트.

    CLAUDE.md §prod-test-runner 자율성: "큰 다운로드 (>100MB) 는 사용자 동의 필요"
    smoke_test.sh line 44~45 경고 인용:
      "최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."

    Returns:
        True: 사용자 동의 / False: 거부 (flow 5 중단)
    """
    print()
    print("=" * 60)
    print(" smoke test 동의 게이트")
    print("=" * 60)
    print()
    print("  smoke test 실행 조건:")
    print("    - 소요 시간: 약 5~15분 (1 step 학습)")
    print("    - 최초 실행 시 모델·데이터셋 다운로드 가능 (svla_so100_pickplace ~100MB 이상)")
    print("    - (smoke_test.sh line 44~45 경고 인용)")
    print()

    return _yn_prompt("위 조건을 이해하고 smoke test 를 실행하겠습니까?", default_yes=True)


def _run_smoke_test(script_dir: Path) -> bool:
    """smoke_test.sh subprocess 호출.

    smoke_test.sh 는 preflight_check.sh 를 내부에서 이미 호출함 (line 30~33).
    timeout 없음 — 5~15분 실행, 사용자 Ctrl+C 로 중단 가능.

    Returns:
        True: 성공 (exit 0) / False: 실패
    """
    smoke_script = script_dir.parent / "scripts" / "smoke_test.sh"

    if not smoke_script.exists():
        print(f"[ERROR] smoke_test.sh 미존재: {smoke_script}", file=sys.stderr)
        return False

    print()
    print("[flow 5] smoke test 시작 (Ctrl+C 로 중단 가능)")
    print()

    result = subprocess.run(
        ["bash", str(smoke_script)],
        check=False,
    )
    return result.returncode == 0


def _select_start_ckpt(script_dir: Path) -> tuple[str, str | None, str | None]:
    """시작 ckpt 케이스 4건 분기 UI.

    레퍼런스: docs/reference/lerobot/src/lerobot/configs/train.py
      - resume: bool = False (L49)
      - checkpoint_path: Path | None = field(init=False, default=None) (L84)
      - elif self.resume: self.checkpoint_path = policy_dir.parent (L94~111)
        → --resume + --config_path=<last>/pretrained_model/train_config.json

    4가지 시작 ckpt 케이스:
      none:           --policy.path=lerobot/smolvla_base (사전학습 시작)
      dummy:          --policy.path=<dummy_ckpt>/pretrained_model (save_dummy_checkpoint.sh 산출물)
      fine-tune-step: --policy.path=<output_dir>/checkpoints/<step>/pretrained_model
      fine-tune-last: --resume (+ config_path 자동 해석: <output_dir>/checkpoints/last/pretrained_model/train_config.json)

    주의: fine-tune-step·fine-tune-last 는 T2 산출물 의존.
          D2 시점엔 코드 분기 정합 만 검증 (실 실행은 T2 완료 후).

    Returns:
        (ckpt_case, policy_path_or_none, config_path_or_none)
        ckpt_case: "none" | "dummy" | "fine-tune-step" | "fine-tune-last"
        policy_path_or_none: --policy.path 값 (fine-tune-last 시 None)
        config_path_or_none: --config_path 값 (fine-tune-last 시만 사용)
    """
    print()
    print("=" * 60)
    print(" 시작 체크포인트 선택")
    print("=" * 60)
    print()
    print("어떤 체크포인트에서 학습을 시작하겠습니까?")
    print()
    print("  1. 사전학습 (none)        — lerobot/smolvla_base 로드 후 fine-tune 시작")
    print("     --policy.path=lerobot/smolvla_base")
    print()
    print("  2. dummy 체크포인트       — save_dummy_checkpoint.sh 산출물 (1 step ckpt)")
    print("     경로: dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/")
    print()
    print("  3. 실 학습 중간 단계      — T2 산출물 필요 (checkpoints/<step>/pretrained_model/)")
    print("     [T2 의존 — D2 시점 코드 분기만 검증, 실 실행은 T2 완료 후]")
    print()
    print("  4. 마지막 저장 (last)     — --resume 으로 이어서 학습")
    print("     경로: dgx/outputs/train/<run>/checkpoints/last/pretrained_model/train_config.json")
    print("     [T2 의존 — D2 시점 코드 분기만 검증]")
    print()
    print("  5. 취소")
    print()

    dgx_dir = str(script_dir.parent)
    dummy_ckpt_path = f"{dgx_dir}/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model"

    while True:
        try:
            raw = _prompt("번호 선택 [1~5, b: 뒤로]: ")
        except KeyboardInterrupt:
            return "none", DEFAULT_POLICY_PATH, None

        # b/back: 데이터셋 선택으로 복귀 신호 — "back" 특수 케이스 반환
        if is_back(raw):
            print()
            print("[ckpt] 뒤로가기 — 데이터셋 선택으로 돌아갑니다.")
            return "back", None, None

        if not raw.isdigit():
            print("  숫자 또는 b(뒤로) 를 입력하세요.")
            continue

        choice = int(raw)

        if choice == 1:
            # none: 사전학습 시작
            print(f"\n[ckpt] 사전학습 시작: --policy.path={DEFAULT_POLICY_PATH}")
            return "none", DEFAULT_POLICY_PATH, None

        elif choice == 2:
            # dummy: save_dummy_checkpoint.sh 산출물
            print(f"\n[ckpt] dummy 체크포인트: {dummy_ckpt_path}")
            return "dummy", dummy_ckpt_path, None

        elif choice == 3:
            # fine-tune-step: 실 학습 중간 체크포인트 경로 입력
            print()
            print("  실 학습 체크포인트 경로 입력 (예: ~/smolvla/dgx/outputs/train/<run>/checkpoints/001000/pretrained_model)")
            try:
                path_input = _prompt("  경로: ")
            except KeyboardInterrupt:
                continue
            if not path_input:
                print("  경로가 비어있습니다. 다시 입력하세요.")
                continue
            print(f"\n[ckpt] fine-tune-step: --policy.path={path_input}")
            return "fine-tune-step", path_input, None

        elif choice == 4:
            # fine-tune-last: --resume + config_path
            print()
            print("  이어서 학습할 run 이름 또는 output_dir 경로 입력")
            print("  (예: ~/smolvla/dgx/outputs/train/<run>)")
            try:
                run_dir = _prompt("  output_dir: ")
            except KeyboardInterrupt:
                continue
            if not run_dir:
                print("  경로가 비어있습니다. 다시 입력하세요.")
                continue
            config_path = f"{run_dir}/checkpoints/last/pretrained_model/train_config.json"
            print(f"\n[ckpt] fine-tune-last: --resume --config_path={config_path}")
            return "fine-tune-last", None, config_path

        elif choice == 5:
            return "none", DEFAULT_POLICY_PATH, None

        else:
            print("  1~5 중 하나를 입력하세요.")


def _run_real_training(
    script_dir: Path,
    scenario: str,
    dataset_repo_id: str,
) -> tuple[bool | str, str | None]:
    """실 학습: lerobot-train draccus 인자 동적 생성 후 실행.

    save_dummy_checkpoint.sh line 56~70 의 lerobot-train 인자 패턴 인용:
      lerobot-train
        --policy.path=lerobot/smolvla_base
        --dataset.repo_id=lerobot/svla_so100_pickplace
        --batch_size=8
        --steps=1
        --log_freq=1
        --save_freq=1
        --save_checkpoint=true        ← line 63 (ckpt 저장 활성)
        --num_workers=4
        --output_dir="${OUTPUT_DIR}"  ← line 25: ${DGX_DIR}/outputs/train/${RUN_NAME}
        --job_name=${RUN_NAME}
        --policy.device=cuda
        --policy.push_to_hub=false
        --rename_map='{"observation.images.overview":"observation.images.camera1",...}'
        --wandb.enable=false

    ckpt 케이스 4건 (TODO-D2 갱신):
      none:           --policy.path=lerobot/smolvla_base
      dummy:          --policy.path=<dummy_ckpt>/pretrained_model
      fine-tune-step: --policy.path=<step>/pretrained_model
      fine-tune-last: --resume --config_path=<last>/pretrained_model/train_config.json
        (레퍼런스: lerobot/configs/train.py L49·L84·L94-111)

    실 학습 시 steps 는 사용자 입력 받음.

    Returns:
        (result, output_dir)
        result: True=성공, False=실패/중단, "CANCELED"=b/back 취소 (학습 미실행)
        output_dir: 학습 출력 디렉터리 경로 또는 None
    """
    import datetime

    run_name_default = f"train_{scenario}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print()
    print("실 학습 파라미터 설정:")
    print(f"  데이터셋:      {dataset_repo_id}")
    print()

    # 시작 ckpt 선택 (4건 분기)
    ckpt_case, policy_path, config_path = _select_start_ckpt(script_dir)

    # b/back 취소: 데이터셋 선택으로 복귀 — "CANCELED" sentinel 반환
    # False 와 구분하여 호출 측(flow5)에서 _show_ckpt_management skip 처리 가능.
    if ckpt_case == "back":
        return "CANCELED", None

    # fine-tune-last 는 resume 모드 — output_dir 은 run_dir 에서 자동 결정됨
    is_resume = (ckpt_case == "fine-tune-last")

    # steps 메뉴 (C0 갱신 — 4개 선택지, default 2000)
    print("학습 step 수 선택:")
    print("  (1) 2000  — 빠른 검증·08 사이클 권장 ★")
    print("  (2) 5000  — 중간")
    print("  (3) 10000 — 본격 학습 (09 사이클 권장)")
    print("  (4) 직접 입력")
    print()

    steps = 2000  # 선언 (루프 break 전 사용 방지)
    while True:
        try:
            raw = _prompt("번호 선택 [1~4, Enter=1 default, b: 뒤로]: ")
        except KeyboardInterrupt:
            return False, None

        if is_back(raw):
            return "CANCELED", None

        if raw == "" or raw == "1":
            steps = 2000
            break
        if raw == "2":
            steps = 5000
            break
        if raw == "3":
            steps = 10000
            break
        if raw == "4":
            try:
                steps_raw = _prompt("학습 steps 직접 입력: ")
            except KeyboardInterrupt:
                return False, None
            if steps_raw.isdigit() and int(steps_raw) > 0:
                steps = int(steps_raw)
                break
            print("  양의 정수를 입력하세요.")
            continue
        print("  1~4 또는 b(뒤로) 를 입력하세요.")

    # run_name 입력 (resume 시에도 출력 구분용)
    try:
        run_name_input = _prompt(f"run 이름 입력 (기본: {run_name_default}): ")
    except KeyboardInterrupt:
        return False, None
    run_name = run_name_input if run_name_input else run_name_default

    # save_freq
    save_freq = max(1, steps // 10)

    # wandb 선택 (C0 안내 강화)
    print()
    print("학습 시각화 옵션:")
    print("  - 기본: 콘솔 tqdm progress bar (자동 — 추가 설정 X)")
    print("  - WandB: 실시간 loss/lr curve 웹 dashboard + eval video")
    print("    (최초 1회 'wandb login' 필요 — DGX 본체 터미널에서)")
    print()
    use_wandb = _yn_prompt("WandB 로깅을 사용하겠습니까? (default: N)", default_yes=False)

    # output_dir: save_dummy_checkpoint.sh line 25 인용
    #   OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"
    dgx_dir = str(script_dir.parent)
    output_dir = f"{dgx_dir}/outputs/train/{run_name}"

    # lerobot-train 인자 구성
    # 레퍼런스: lerobot/configs/train.py
    #   resume=False (L49): --policy.path 로 시작
    #   resume=True (L94):  --resume + --config_path=<train_config.json 경로>
    if is_resume:
        # fine-tune-last: --resume 모드
        # train.py L94-111: resume 시 config_path 에서 checkpoint_path 결정
        cmd = [
            "lerobot-train",
            "--resume",
            f"--config_path={config_path}",
            f"--dataset.repo_id={dataset_repo_id}",
            "--batch_size=8",
            f"--steps={steps}",
            "--log_freq=50",
            f"--save_freq={save_freq}",
            "--save_checkpoint=true",
            "--num_workers=4",
            f"--job_name={run_name}",
            "--policy.device=cuda",
            "--policy.push_to_hub=false",
            "--rename_map={\"observation.images.overview\":\"observation.images.camera1\","
            "\"observation.images.wrist_left\":\"observation.images.camera2\"}",
            f"--wandb.enable={'true' if use_wandb else 'false'}",
        ]
    else:
        # none / dummy / fine-tune-step: --policy.path 로 시작
        cmd = [
            "lerobot-train",
            f"--policy.path={policy_path}",
            f"--dataset.repo_id={dataset_repo_id}",
            "--batch_size=8",
            f"--steps={steps}",
            "--log_freq=50",
            f"--save_freq={save_freq}",
            "--save_checkpoint=true",
            "--num_workers=4",
            f"--output_dir={output_dir}",
            f"--job_name={run_name}",
            "--policy.device=cuda",
            "--policy.push_to_hub=false",
            "--rename_map={\"observation.images.overview\":\"observation.images.camera1\","
            "\"observation.images.wrist_left\":\"observation.images.camera2\"}",
            f"--wandb.enable={'true' if use_wandb else 'false'}",
        ]

    print()
    print("=" * 60)
    print(" 실 학습 시작")
    print("=" * 60)
    print(f"  ckpt 케이스: {ckpt_case}")
    if is_resume:
        print(f"  config_path: {config_path}")
    else:
        print(f"  policy:      {policy_path}")
        print(f"  output_dir:  {output_dir}")
    print(f"  run:         {run_name}")
    print(f"  steps:       {steps}")
    print(f"  save_freq:   {save_freq}")
    print()
    print("  (Ctrl+C 로 중단 가능 — 마지막 save_checkpoint 까지 저장됨)")
    print("  ※ lerobot-train 실행 중에는 뒤로가기 불가 — Ctrl+C 로만 종료 가능.")
    print("=" * 60)
    print()

    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        return True, output_dir if not is_resume else None
    else:
        print(f"\n[ERROR] lerobot-train 종료 코드: {result.returncode}")
        return False, output_dir if not is_resume else None


def _show_ckpt_management(output_dir: str | None) -> None:
    """ckpt 관리: 저장 경로 출력 + 케이스 목록 표시 + 사용자 선택.

    14_dgx_cli_flow.md §5-3 ckpt 전송 분기 UI:
      케이스 1·2 → devPC 에서 sync_ckpt_dgx_to_orin.sh 실행
      케이스 3   → 차기 사이클 신규 예정 (DataCollector 우회 무효 — 06 결정)
      나중에     → 안내만
    """
    print()
    print("=" * 60)
    print(" ckpt 관리 — 전송 안내")
    print("=" * 60)
    print()

    if output_dir:
        # save_dummy_checkpoint.sh line 25 인용:
        #   체크포인트: ${OUTPUT_DIR}/checkpoints/000001/pretrained_model/
        print("  학습 출력 디렉터리:")
        print(f"    {output_dir}")
        print(f"    (체크포인트: {output_dir}/checkpoints/<step>/pretrained_model/)")
    else:
        print("  출력 디렉터리 정보 없음 — DGX 의 dgx/outputs/train/ 을 직접 확인하세요.")

    print()
    print("체크포인트를 Orin 에 전송하겠습니까?")
    print()

    case_keys = list(CKPT_CASES.keys())
    for key in case_keys:
        c = CKPT_CASES[key]
        print(f"  {key}. {c['label']}")

    quit_num = len(case_keys) + 1
    print(f"  {quit_num}. 종료 (전송 안 함)")
    print()
    print("  * 모든 전송 스크립트는 devPC 에서 실행하는 명령입니다.")
    print("    DGX 에서 직접 rsync 호출 X.")
    print()

    while True:
        try:
            raw = _prompt(f"번호 선택 [1~{quit_num}, b: 건너뜀]: ")
        except KeyboardInterrupt:
            print()
            print("[ckpt 관리] 종료합니다.")
            return

        # b/back: ckpt 전송 건너뜀 (종료와 동일)
        if is_back(raw):
            print("[ckpt 관리] 전송 건너뜀 — 나중에 docs/storage/others/ckpt_transfer_scenarios.md 참조.")
            return

        if not raw.isdigit():
            print("  숫자 또는 b(건너뜀) 를 입력하세요.")
            continue

        choice_str = raw

        if choice_str == str(quit_num):
            print("[ckpt 관리] 전송 생략 — 나중에 docs/storage/others/ckpt_transfer_scenarios.md 참조.")
            return

        if choice_str in CKPT_CASES:
            c = CKPT_CASES[choice_str]
            print()
            print(f"[{c['label']}]")
            print()
            print(c["guide"])
            return

        print(f"  유효한 번호를 입력하세요 (1~{quit_num}) 또는 b(건너뜀).")


def flow5_train_and_manage_ckpt(
    script_dir: Path,
    scenario: str,
    dataset_repo_id: str,
) -> bool:
    """flow 5: 학습 실행 + ckpt 관리 통합.

    smoke 분기:
      동의 게이트 → smoke_test.sh subprocess 호출
    실 학습 분기:
      lerobot-train draccus 인자 동적 생성 → 호출
    공통:
      학습 완료 후 ckpt 경로 출력 + 케이스 목록 + 사용자 선택

    Returns:
        True: 학습 완료 (성공·실패 무관, 사용자가 진행 완료) / False: 사용자 중단
    """
    print()
    print("=" * 60)
    print(" flow 5 — 학습 실행")
    print("=" * 60)
    print()
    print(f"  시나리오: {SCENARIOS[scenario]['label']}")
    print(f"  데이터셋: {dataset_repo_id}")
    print()

    output_dir: str | None = None

    if scenario == "smoke":
        # smoke_test.sh 는 --save_checkpoint=false (line 75) → ckpt 없음
        # 동의 게이트 (CLAUDE.md §prod-test-runner 자율성 정책)
        if not _smoke_consent_gate():
            print("[flow 5] smoke test 취소.")
            return False

        success = _run_smoke_test(script_dir)

        if success:
            print()
            print("[flow 5] smoke test 완료.")
            print("  smoke test 는 체크포인트를 저장하지 않습니다.")
            print("  (smoke_test.sh line 75: --save_checkpoint=false)")
            print()
            print("  실 학습 체크포인트 생성 필요 시:")
            print("    시나리오 s1/s3/lora 를 선택하거나,")
            print("    dgx/scripts/save_dummy_checkpoint.sh 를 직접 실행하세요.")
            # smoke 는 ckpt 관리 불필요 — 저장 없음
        else:
            print()
            print("[flow 5] smoke test 실패. smoke_test.sh 출력을 확인하세요.")

        return success

    else:
        # 실 학습
        result, output_dir = _run_real_training(script_dir, scenario, dataset_repo_id)

        # b/back 취소: 학습 미실행 — ckpt 관리 UI skip (학습이 없었으므로 안내 불필요)
        if result == "CANCELED":
            print()
            print("[flow 5] 뒤로가기 — 데이터셋 선택으로 돌아갑니다.")
            return False

        success = bool(result)

        if success:
            print()
            print("[flow 5] 학습 완료.")
        else:
            print()
            print("[flow 5] 학습이 오류 또는 중단으로 종료되었습니다.")
            if output_dir:
                print(f"  출력 디렉터리: {output_dir}")
                print("  체크포인트가 일부 저장되어 있을 수 있습니다.")

        # ckpt 관리 (성공·실패 무관 — 일부 저장 가능성 있으므로)
        _show_ckpt_management(output_dir)
        return success


# ---------------------------------------------------------------------------
# 진입점 — entry.py 에서 호출
# ---------------------------------------------------------------------------

def run_training_flow(script_dir: Path) -> int:
    """flow 3~5 순차 실행.

    entry.py 의 dgx 분기에서 호출:
      from flows.training import run_training_flow
      return run_training_flow(script_dir)

    Args:
        script_dir: dgx/interactive_cli/ 디렉터리 경로

    Returns:
        0: 정상 완료 / 1: 오류 또는 사용자 중단
    """
    try:
        # flow 3: 시나리오 선택
        scenario = flow3_select_scenario(script_dir)
        if scenario is None:
            return 0  # 사용자 종료 선택

        # flow 4: 데이터셋 선택
        dataset_repo_id = flow4_select_dataset(script_dir, scenario)
        if dataset_repo_id is None:
            return 0  # 사용자 종료 선택

        # flow 5: 학습 + ckpt 관리
        success = flow5_train_and_manage_ckpt(script_dir, scenario, dataset_repo_id)

        return 0 if success else 1

    except KeyboardInterrupt:
        print()
        print("[training] Ctrl+C — 종료합니다.")
        return 0


def run_training_flow_with_dataset(
    script_dir: Path,
    dataset_name: str | None = None,
) -> int:
    """flow 3~5 순차 실행 — G-4 수집 후 학습 전환 시 dataset_name 자동 선택.

    mode.py 의 G-4 학습 전환 prompt 에서 호출:
      from flows.training import run_training_flow_with_dataset
      return run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)

    dataset_name 이 주어지면 flow 4 에서 자동 선택 (사용자 입력 없이 진행).
    dataset_name 이 None 이면 run_training_flow 와 동일 (flow 4 사용자 입력).

    Args:
        script_dir: dgx/interactive_cli/ 디렉터리 경로
        dataset_name: 방금 수집한 데이터셋 이름 (repo_id 의 <name> 부분)
                      G-4 에서 ~/smolvla/dgx/data/<dataset_name> 로 자동 매핑.

    Returns:
        0: 정상 완료 / 1: 오류 또는 사용자 중단
    """
    try:
        # flow 3: 시나리오 선택
        scenario = flow3_select_scenario(script_dir)
        if scenario is None:
            return 0

        # flow 4: 데이터셋 선택 (dataset_name 자동 선택 또는 사용자 입력)
        if dataset_name and scenario != "smoke":
            # G-4: 방금 수집한 데이터셋 자동 선택
            local_path = f"~/smolvla/dgx/data/{dataset_name}"
            print()
            print(f"[training] 방금 수집한 데이터셋 자동 선택: {local_path}")
            dataset_repo_id = local_path
        else:
            dataset_repo_id = flow4_select_dataset(script_dir, scenario)
            if dataset_repo_id is None:
                return 0

        # flow 5: 학습 + ckpt 관리
        success = flow5_train_and_manage_ckpt(script_dir, scenario, dataset_repo_id)

        return 0 if success else 1

    except KeyboardInterrupt:
        print()
        print("[training] Ctrl+C — 종료합니다.")
        return 0
