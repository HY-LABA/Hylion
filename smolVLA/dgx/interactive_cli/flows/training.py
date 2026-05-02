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
  - scripts/sync_ckpt_dgx_to_datacollector.sh — 직접 Read (line 6~36)
    (devPC 전용 스크립트 — DGX 에서 직접 호출 X, 안내 출력만)
"""

import subprocess
import sys
from pathlib import Path


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

# ckpt 케이스 안내 (sync_ckpt_dgx_to_datacollector.sh line 19~22 인용)
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
        "label": "케이스 3 — 시연장 Orin 인터넷 격리 (DataCollector 우회)",
        "guide": (
            "devPC 에서 실행:\n"
            "  bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh\n"
            "  또는 특정 run 지정:\n"
            "  bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --run <run_name>\n"
            "\n"
            "  이후 DataCollector -> Orin 전송은 DataCollector 에서 수동 수행.\n"
            "  (docs/storage/others/ckpt_transfer_scenarios.md §3 참조)\n"
        ),
    },
    "3": {
        "label": "나중에 직접 전송 (안내만)",
        "guide": (
            "전송 방법:\n"
            "  docs/storage/others/ckpt_transfer_scenarios.md 에서\n"
            "  케이스 1~4 중 해당하는 절차를 따르세요.\n"
        ),
    },
    "4": {
        "label": "케이스 4 — USB 드라이브 전송",
        "guide": (
            "USB 드라이브 절차:\n"
            "  docs/storage/others/ckpt_transfer_scenarios.md §4 를 따르세요.\n"
            "\n"
            "  (sync_ckpt_dgx_to_datacollector.sh line 22 인용:\n"
            "   케이스 4: Orin USB 드라이브만 가능 → USB 절차)\n"
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
            raw = _prompt(f"번호 선택 [1~{len(scenario_keys) + 1}]: ")
        except KeyboardInterrupt:
            return None

        if not raw.isdigit():
            print("  숫자를 입력하세요.")
            continue

        choice = int(raw)

        if choice == len(scenario_keys) + 1:
            print("종료합니다.")
            return None

        if 1 <= choice <= len(scenario_keys):
            selected = scenario_keys[choice - 1]
            print(f"\n[선택] {SCENARIOS[selected]['label']}")
            return selected

        print(f"  유효한 번호를 입력하세요 (1~{len(scenario_keys) + 1}).")


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
            raw = _prompt("번호 선택 [1~4]: ")
        except KeyboardInterrupt:
            return None

        if not raw.isdigit():
            print("  숫자를 입력하세요.")
            continue

        choice = int(raw)

        if choice == 4:
            print("종료합니다.")
            return None

        if choice == 1:
            # HF Hub repo_id 직접 입력
            try:
                repo_id = _prompt("HF Hub repo_id 입력 (예: lerobot/svla_so100_pickplace): ")
            except KeyboardInterrupt:
                return None
            if not repo_id:
                print("  repo_id 가 비어있습니다. 다시 입력하세요.")
                continue
            print(f"\n[선택] HF Hub: {repo_id}")
            return repo_id

        if choice == 2:
            if not local_datasets:
                print("  로컬 데이터셋이 없습니다. 먼저 DataCollector 에서 rsync 를 실행하세요.")
                continue
            return _select_local_dataset(local_datasets)

        if choice == 3:
            print(f"\n[선택] 기본 데이터셋: {SMOKE_DEFAULT_DATASET}")
            return SMOKE_DEFAULT_DATASET

        print("  유효한 번호를 입력하세요 (1~4).")


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
            raw = _prompt(f"번호 선택 [1~{len(local_datasets) + 1}]: ")
        except KeyboardInterrupt:
            return None

        if not raw.isdigit():
            print("  숫자를 입력하세요.")
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

        print(f"  유효한 번호를 입력하세요 (1~{len(local_datasets) + 1}).")


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


def _run_real_training(
    script_dir: Path,
    scenario: str,
    dataset_repo_id: str,
) -> tuple[bool, str | None]:
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
        --rename_map='{"observation.images.top":"observation.images.camera1",...}'
        --wandb.enable=false

    실 학습 시 steps 는 사용자 입력 받음.

    Returns:
        (성공 여부, output_dir 경로 문자열 또는 None)
    """
    import datetime

    run_name_default = f"train_{scenario}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print()
    print("실 학습 파라미터 설정:")
    print(f"  기본 policy:   {DEFAULT_POLICY_PATH}")
    print(f"  데이터셋:      {dataset_repo_id}")
    print()

    # steps 입력
    while True:
        try:
            steps_raw = _prompt("학습 steps 입력 (기본: 10000): ")
        except KeyboardInterrupt:
            return False, None
        if steps_raw == "":
            steps = 10000
            break
        if steps_raw.isdigit() and int(steps_raw) > 0:
            steps = int(steps_raw)
            break
        print("  양의 정수를 입력하세요.")

    # run_name 입력
    try:
        run_name_input = _prompt(f"run 이름 입력 (기본: {run_name_default}): ")
    except KeyboardInterrupt:
        return False, None
    run_name = run_name_input if run_name_input else run_name_default

    # save_freq
    save_freq = max(1, steps // 10)

    # wandb 선택
    use_wandb = _yn_prompt("WandB 로깅을 사용하겠습니까?", default_yes=False)

    # output_dir: save_dummy_checkpoint.sh line 25 인용
    #   OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"
    dgx_dir = str(script_dir.parent)
    output_dir = f"{dgx_dir}/outputs/train/{run_name}"

    cmd = [
        "lerobot-train",
        f"--policy.path={DEFAULT_POLICY_PATH}",
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
        "--rename_map={\"observation.images.top\":\"observation.images.camera1\","
        "\"observation.images.wrist\":\"observation.images.camera2\"}",
        f"--wandb.enable={'true' if use_wandb else 'false'}",
    ]

    print()
    print("=" * 60)
    print(" 실 학습 시작")
    print("=" * 60)
    print(f"  run:        {run_name}")
    print(f"  steps:      {steps}")
    print(f"  save_freq:  {save_freq}")
    print(f"  output_dir: {output_dir}")
    print()
    print("  (Ctrl+C 로 중단 가능 — 마지막 save_checkpoint 까지 저장됨)")
    print("=" * 60)
    print()

    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        return True, output_dir
    else:
        print(f"\n[ERROR] lerobot-train 종료 코드: {result.returncode}")
        return False, output_dir


def _show_ckpt_management(output_dir: str | None) -> None:
    """ckpt 관리: 저장 경로 출력 + 케이스 목록 표시 + 사용자 선택.

    14_dgx_cli_flow.md §5-3 ckpt 전송 분기 UI:
      케이스 1·2 → devPC 에서 sync_ckpt_dgx_to_orin.sh 실행
      케이스 3   → devPC 에서 sync_ckpt_dgx_to_datacollector.sh 실행
      나중에     → 안내만

    sync_ckpt_dgx_to_datacollector.sh line 19~22 케이스 설명 인용:
      케이스 1: 동일 광역 네트워크 → sync_ckpt_dgx_to_orin.sh 직접
      케이스 2: Orin 인터넷 가능, 다른 서브넷 → 2-hop
      케이스 3: Orin 인터넷 격리 → 본 스크립트 (DataCollector 우회)
      케이스 4: USB 드라이브
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
            raw = _prompt(f"번호 선택 [1~{quit_num}]: ")
        except KeyboardInterrupt:
            print()
            print("[ckpt 관리] 종료합니다.")
            return

        if not raw.isdigit():
            print("  숫자를 입력하세요.")
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

        print(f"  유효한 번호를 입력하세요 (1~{quit_num}).")


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
        success, output_dir = _run_real_training(script_dir, scenario, dataset_repo_id)

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
