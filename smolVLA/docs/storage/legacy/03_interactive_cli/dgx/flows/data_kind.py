"""interactive_cli flow 5 — 학습 종류 선택.

5개 옵션 메뉴 (D1 §3 매핑 표 적용, 사용자 결정 2026-05-02 옵션 1 단순 pick-place 권장):

| # | 이름 | task instruction | 권장 에피소드 | episode_time_s | reset_time_s |
|---|---|---|---|---|---|
| 1 | 단순 pick-place (권장) | "Pick up the object and place it in the target area." | 50 | 12 | 5 |
| 2 | push (밀기) | "Push the object to the target position." | 30~50 | 8 | 5 |
| 3 | stack (쌓기) | "Pick up the block and stack it on top of the other block." | 50~100 | 15 | 7 |
| 4 | drawer open/close | "Open the drawer." | 30~50 | 10 | 5 |
| 5 | handover (물건 전달) | "Pick up the object and hand it over." | 30~50 | 10 | 5 |

레퍼런스 (이식 원본):
  docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/data_kind.py
  DATA_KIND_OPTIONS·DataKindResult·flow5_select_data_kind() 그대로 재사용.

이식 변경 사항 (14_dgx_cli_flow.md §3-3):
  - 변경 없음. 데이터 종류 상수·로직이 노드(datacollector vs dgx)에 독립적.
  - DATA_KIND_OPTIONS 5개 옵션 그대로 (X1 study §3 명시 — 변경 없음).

"""

from typing import NamedTuple

from flows._back import is_back


# ---------------------------------------------------------------------------
# 학습 종류 상수 (D1 §3 매핑 표 그대로)
# ---------------------------------------------------------------------------

# 사용자 결정 2026-05-02: 옵션 (1) 단순 pick-place — svla_so100_pickplace 분포 동일
# instruction: "Pick up the object and place it in the target area."
# 권장 에피소드: 50

DATA_KIND_OPTIONS: dict[int, dict] = {
    1: {
        "name": "단순 pick-place",
        "description": "책상 위 물체를 집어 지정 위치에 놓기",
        "note": "SmolVLA 사전학습(svla_so100_pickplace) 분포에 가장 가까움 — 권장",
        "single_task": "Pick up the object and place it in the target area.",
        "default_num_episodes": 50,
        "episode_range": "50",
        "default_episode_time_s": 12,  # lego pick-place 한 사이클 ~10초 + 여유 2초
        "default_reset_time_s": 5,
    },
    2: {
        "name": "push (밀기)",
        "description": "물체를 한 위치에서 다른 위치로 밀기",
        "note": "그리퍼 클로즈 없이 팔 움직임 위주",
        "single_task": "Push the object to the target position.",
        "default_num_episodes": 40,
        "episode_range": "30~50",
        "default_episode_time_s": 8,   # 밀기 동작 짧음
        "default_reset_time_s": 5,
    },
    3: {
        "name": "stack (쌓기)",
        "description": "블록을 다른 블록 위에 쌓기",
        "note": "pick-place 보다 정밀도 요구",
        "single_task": "Pick up the block and stack it on top of the other block.",
        "default_num_episodes": 75,
        "episode_range": "50~100",
        "default_episode_time_s": 15,  # 정밀도 + 두 단계
        "default_reset_time_s": 7,
    },
    4: {
        "name": "drawer open/close",
        "description": "서랍 열고 닫기",
        "note": "지속적 힘 인가 동작",
        "single_task": "Open the drawer.",
        "default_num_episodes": 40,
        "episode_range": "30~50",
        "default_episode_time_s": 10,  # 단일 동작
        "default_reset_time_s": 5,
    },
    5: {
        "name": "handover (물건 전달)",
        "description": "물체를 집어 사람 손 방향으로 가져다 주기",
        "note": "",
        "single_task": "Pick up the object and hand it over.",
        "default_num_episodes": 40,
        "episode_range": "30~50",
        "default_episode_time_s": 10,  # pick + 전달
        "default_reset_time_s": 5,
    },
}


class DataKindResult(NamedTuple):
    """flow 5 선택 결과. record.py 로 전달."""
    choice: int           # 선택 번호 (1~5)
    single_task: str      # lerobot-record --dataset.single_task 값
    default_num_episodes: int  # 권장 에피소드 수
    default_episode_time_s: int  # 에피소드 당 녹화 시간 기본값 (초)
    default_reset_time_s: int    # 에피소드 간 리셋 시간 기본값 (초)


# ---------------------------------------------------------------------------
# flow 5 메인 함수
# ---------------------------------------------------------------------------

def flow5_select_data_kind() -> "DataKindResult | None":
    """flow 5: 학습 종류 선택 메뉴.

    원본 datacollector data_kind.py flow5_select_data_kind() 그대로.
    "어떤 학습 데이터를 모을건가요?" + 5개 옵션 중 선택.

    Returns:
        DataKindResult: 선택 결과 / None: 종료 선택 또는 Ctrl+C
    """
    print()
    print("=" * 60)
    print(" flow 5 — 학습 종류 선택")
    print("=" * 60)
    print()
    print("어떤 학습 데이터를 모을건가요?")
    print()

    for num, opt in DATA_KIND_OPTIONS.items():
        note_str = f"  ({opt['note']})" if opt["note"] else ""
        recommend = " ★ 권장" if num == 1 else ""
        print(f"  ({num}) {opt['name']}{recommend}")
        print(f"       {opt['description']}{note_str}")
        print(f"       task: \"{opt['single_task']}\"")
        print(f"       권장 에피소드: {opt['episode_range']}")
        print()

    print(f"  ({len(DATA_KIND_OPTIONS) + 1}) 종료")
    print()

    while True:
        try:
            raw = input(f"번호 선택 [1~{len(DATA_KIND_OPTIONS) + 1}, b: 뒤로]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 5] 종료됩니다.")
            return None

        # b/back: 직전 분기점 (precheck) 으로 복귀
        if is_back(raw):
            print()
            print("[flow 5] 뒤로가기 — teleop 사전 점검 단계로 돌아갑니다.")
            return None

        if not raw.isdigit():
            print("  숫자 또는 b(뒤로) 를 입력하세요.")
            continue

        choice = int(raw)

        if choice == len(DATA_KIND_OPTIONS) + 1:
            print("[flow 5] 종료합니다.")
            return None

        if choice in DATA_KIND_OPTIONS:
            opt = DATA_KIND_OPTIONS[choice]
            print()
            print(f"[선택] ({choice}) {opt['name']}")
            print(f"  task instruction: \"{opt['single_task']}\"")
            print(f"  권장 에피소드: {opt['episode_range']}")
            print(f"  기본 에피소드 시간: {opt['default_episode_time_s']}초")
            print(f"  기본 리셋 시간:     {opt['default_reset_time_s']}초")
            return DataKindResult(
                choice=choice,
                single_task=opt["single_task"],
                default_num_episodes=opt["default_num_episodes"],
                default_episode_time_s=opt["default_episode_time_s"],
                default_reset_time_s=opt["default_reset_time_s"],
            )

        print(f"  유효한 번호를 입력하세요 (1~{len(DATA_KIND_OPTIONS) + 1}) 또는 b(뒤로).")
