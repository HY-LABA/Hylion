"""interactive_cli flow 3 — mode 분기 (수집 / 학습 / 종료).

사용자 결정 G-4 (06_dgx_absorbs_datacollector, 2026-05-02):
  메뉴: (1) 수집 / (2) 학습 / (3) 종료
  (1) 수집 선택 시 → 수집 flow 3~7 (teleop → data_kind → record → transfer) 완주
  수집 완주 후   → "수집 완료. 바로 학습으로 진행할까요? [Y/n]" prompt
    Y → 학습 mode flow 3~ 자동 진입 (방금 수집한 dataset_name 을 training 에 인계)
    n → 저장 안내 + 종료
  (2) 학습 선택 시 → 학습 flow 3~ (run_training_flow)
  (3) 종료 선택 시 → 즉시 종료

갱신 (2026-05-04, TODO-D4):
  수집 mode (1) 에 teleop 진입 직전 사전 점검 단계 추가 (ANOMALIES 07-#3 후속).
  흐름: env_check(mode="collect") PASS → teleop_precheck() → _run_collect_flow()
  teleop_precheck(): 저장된 모터 포트·카메라 인덱스·캘리브 위치 표시 + 3-way 분기.
  "cancel" 시 return 0 (수집 mode 정상 종료).

갱신 (2026-05-03, TODO-D6):
  flow3_mode_entry() 에 display_mode 인자 추가.
  수집 mode (1) → teleop_precheck(script_dir, display_mode) 로 전달.
  precheck.py 가 카메라 식별 시 display_mode ("direct"/"ssh") 에 따라
  OpenCV imshow 또는 이미지 파일 저장으로 영상 표시.

구조: 단발 종료 (G-1 기반) + 수집 끝 학습 전환 prompt 하이브리드.
      메뉴 진입 후 mode 완료 시 종료 (루프 X).

레퍼런스:
  - 14_dgx_cli_flow.md §2 G-1~G-4 후보 분석 + G-4 확정
  - datacollector/interactive_cli/flows/{teleop,data_kind,record,transfer}.py 이식 패턴
  - dgx/interactive_cli/flows/training.py run_training_flow() 시그니처
  - dgx/interactive_cli/flows/precheck.py teleop_precheck() — TODO-D4 신규
"""

from pathlib import Path


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
# 수집 flow 실행 (flow 3~7)
# ---------------------------------------------------------------------------

def _run_collect_flow(script_dir: Path) -> tuple[int, str | None]:
    """수집 flow (teleop → data_kind → record → transfer) 완주.

    14_dgx_cli_flow.md §3 수집 mode flow 3·4·5·6·7 그대로.

    Args:
        script_dir: dgx/interactive_cli/ 경로

    Returns:
        (returncode, dataset_name_or_None)
        dataset_name: G-4 학습 전환 시 training flow 에 인계하는 데이터셋 이름
    """
    from flows.teleop import flow3_teleoperate, flow4_confirm_teleop
    from flows.data_kind import flow5_select_data_kind
    from flows.record import flow6_record
    from flows.transfer import flow7_select_transfer

    # flow 3: 텔레오퍼레이션
    rc = flow3_teleoperate(script_dir)

    # flow 4: 텔레오퍼레이션 완료 확인
    if not flow4_confirm_teleop(script_dir, rc):
        return 1, None

    # flow 5: 학습 종류 선택
    data_kind_result = flow5_select_data_kind()
    if data_kind_result is None:
        return 1, None

    # flow 6: lerobot-record 실행
    # D12: configs_dir 전달 — cameras.json·ports.json 로드 후 인자 갱신.
    # cameras.json 미설정 시 hardcoded fallback (wrist_left=0, overview=1) 사용.
    # precheck.py _get_configs_dir 패턴과 동일하게 configs_dir 계산.
    configs_dir = script_dir / "configs"
    success, local_dataset_path, repo_id = flow6_record(
        data_kind_choice=data_kind_result.choice,
        single_task=data_kind_result.single_task,
        default_num_episodes=data_kind_result.default_num_episodes,
        configs_dir=configs_dir,
    )

    # dataset_name 추출 (G-4 학습 전환 인계용)
    dataset_name: str | None = None
    if repo_id:
        dataset_name = repo_id.split("/")[-1]

    # flow 7: 전송 방식 선택
    # transfer.py 는 선택된 전송 완료 후 결과만 반환 (G-4 학습 전환 prompt 는 mode.py 책임)
    flow7_select_transfer(script_dir, local_dataset_path, repo_id)

    if not success:
        return 1, dataset_name

    return 0, dataset_name


# ---------------------------------------------------------------------------
# 수집 후 학습 전환 prompt (G-4 핵심)
# ---------------------------------------------------------------------------

def _prompt_transition_to_train(
    script_dir: Path,
    dataset_name: str | None,
) -> int:
    """수집 완료 후 학습 전환 prompt.

    G-4 명세:
      "수집 완료. 바로 학습으로 진행할까요? [Y/n]"
      Y → 학습 mode flow 3~ 자동 진입 (방금 수집 dataset_name 을 dataset_id 로 인계)
      n → 저장 안내 + 종료

    Args:
        script_dir: dgx/interactive_cli/ 경로
        dataset_name: record.py 가 수집한 데이터셋 이름 (repo_id 의 <name> 부분)

    Returns:
        0: 정상 완료 / 1: 오류
    """
    print()
    print("=" * 60)
    print(" 수집 완료")
    print("=" * 60)
    print()
    if dataset_name:
        print(f"  수집된 데이터셋: {dataset_name}")
        print(f"  저장 경로: ~/smolvla/dgx/data/{dataset_name}")
    print()

    go_train = _yn_prompt("수집 완료. 바로 학습으로 진행할까요?", default_yes=True)

    if not go_train:
        print()
        print("[mode] 수집 완료 후 종료합니다.")
        if dataset_name:
            print(f"  데이터셋 저장 경로: ~/smolvla/dgx/data/{dataset_name}")
            print("  나중에 학습하려면 bash dgx/interactive_cli/main.sh 를 다시 실행하세요.")
        return 0

    # 학습 mode 자동 진입 (dataset_name 인계)
    print()
    print("[mode] 학습 mode 로 자동 진입합니다.")
    if dataset_name:
        print(f"  방금 수집한 데이터셋 자동 선택: {dataset_name}")
    print()

    from flows.training import run_training_flow_with_dataset
    return run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)


# ---------------------------------------------------------------------------
# flow 3 메인 — mode 선택 진입점
# ---------------------------------------------------------------------------

def flow3_mode_entry(script_dir: Path, display_mode: str = "ssh") -> int:
    """flow 3: mode 선택 메뉴 + 해당 flow 실행.

    G-4 명세 적용:
      메뉴: (1) 수집 / (2) 학습 / (3) 종료
      (1) 수집 완주 후 → 학습 전환 prompt
      (2) 학습 flow 직접 진입
      (3) 즉시 종료

    단발 종료 구조 (루프 X).

    Args:
        script_dir: dgx/interactive_cli/ 경로
        display_mode: "direct" (DGX 모니터 OpenCV imshow) | "ssh" (이미지 파일 저장)
                      entry.py detect_display_mode() 결과 전달 (TODO-D6).
                      기본값 "ssh" — 안전한 fallback.

    Returns:
        0: 정상 완료 / 1: 오류
    """
    print()
    print("=" * 60)
    print(" flow 3 — mode 선택")
    print("=" * 60)
    print()
    print("무엇을 하겠습니까?")
    print()
    print("  (1) 데이터 수집 → teleoperation → record → transfer")
    print("  (2) 학습        → 시나리오 선택 → 데이터셋 → 학습 + ckpt 관리")
    print("  (3) 종료")
    print()

    while True:
        try:
            raw = _prompt("번호 선택 [1~3]: ")
        except KeyboardInterrupt:
            print()
            print("[mode] 종료합니다.")
            return 0

        if raw == "1":
            # 수집 mode
            print()
            print("[mode] 데이터 수집 mode 진입합니다.")
            print()

            # env_check.py 수집 환경 체크 (항목 6~9: USB·dialout·v4l2·SO-ARM 포트 응답)
            # entry.py 에서는 scenario="smoke" 로 preflight 만 실행 (학습 mode 공통 사전 점검).
            # 수집 mode 에서는 SO-ARM·카메라 하드웨어 체크 추가 (env_check.py mode="collect").
            # 결정 (TODO-X2 §7, env_check.py docstring): selective check — 수집 mode 에서만 항목 6~9 실행.
            # FAIL 시 사용자 안내 후 종료 (실 SO-ARM 없는 환경 보호).
            from flows.env_check import flow2_env_check as _flow2_env_check_collect
            if not _flow2_env_check_collect(script_dir, scenario="smoke", mode="collect"):
                print()
                print("[mode] 수집 환경 체크 FAIL — SO-ARM·카메라 연결 후 재시작하세요.")
                return 1

            # teleop 진입 직전 사전 점검 (TODO-D4 신규 단계, TODO-D6 display_mode 추가)
            # 저장된 모터 포트·카메라 인덱스·캘리브 위치 표시 + 분기:
            #   "proceed" → teleop 진행
            #   "cancel"  → 수집 mode 종료
            # display_mode: 카메라 영상 표시 방법 ("direct"/"ssh") — entry.py 에서 전달.
            from flows.precheck import teleop_precheck as _teleop_precheck
            precheck_result = _teleop_precheck(script_dir, display_mode=display_mode)
            if precheck_result == "cancel":
                print()
                print("[mode] 사전 점검에서 취소를 선택했습니다. 수집 mode 를 종료합니다.")
                return 0

            rc, dataset_name = _run_collect_flow(script_dir)

            if rc != 0:
                print()
                print("[mode] 수집 flow 가 오류 또는 중단으로 종료되었습니다.")
                return rc

            # G-4: 수집 완료 후 학습 전환 prompt
            return _prompt_transition_to_train(script_dir, dataset_name)

        elif raw == "2":
            # 학습 mode
            print()
            print("[mode] 학습 mode 진입합니다.")
            print()

            from flows.training import run_training_flow
            return run_training_flow(script_dir)

        elif raw == "3":
            print()
            print("[mode] 종료합니다.")
            return 0

        else:
            print("  1, 2, 3 중 하나를 입력하세요.")
