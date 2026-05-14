#!/usr/bin/env python3
"""dgx/finetune/leftarm_v2/check_port_and_camera_index.py

lerobot-find-port (follower·leader 2회) + lerobot-find-cameras 를 순차 실행해
config/base_config.yaml 의 hardware 섹션에 입력할 4개 값을 찾는 도우미.

사용:
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  python check_port_and_camera_index.py

각 단계는 인터랙티브 (lerobot-find-port 는 USB 를 뽑았다 꽂아 식별 — 1회당 포트 1개).
찾은 값은 직접 config/base_config.yaml 의 hardware 섹션에 입력한다 (env 아님 — run_record.py 가
그 yaml 값을 읽음). 자동 기록하지 않음 — 사용자가 확인 후 직접 입력.

USB enumeration 은 부팅·재연결마다 바뀔 수 있으므로 매 세션 시작 시 재확인 권장.
"""
import shutil
import subprocess
import sys

CAMERA_OUTPUT_DIR = "/tmp/lerobot_camera_check"

STEPS = [
    ("1/3", "FOLLOWER 포트 (lerobot-find-port)",
     ["lerobot-find-port"],
     ["follower·leader 양쪽 USB 가 모두 연결된 상태에서 시작.",
      "안내가 나오면 → SO-101 *follower* 팔의 USB 만 뽑고 Enter.",
      "→ 사라진 포트가 follower_port (예: /dev/ttyACM0)."]),
    ("2/3", "LEADER 포트 (lerobot-find-port)",
     ["lerobot-find-port"],
     ["⚠️ 먼저 follower USB 를 *다시 연결* (양쪽 다 연결된 상태여야 함).",
      "안내가 나오면 → SO-101 *leader* 팔의 USB 만 뽑고 Enter.",
      "→ 사라진 포트가 leader_port (예: /dev/ttyACM1)."]),
    ("3/3", "카메라 인덱스 (lerobot-find-cameras)",
     ["lerobot-find-cameras", "opencv", "--output-dir", CAMERA_OUTPUT_DIR],
     ["top·wrist 카메라 연결 확인 (스캔만 — USB 뽑을 필요 없음).",
      f"캡처 이미지가 {CAMERA_OUTPUT_DIR}/ 에 저장됨 — 이미지를 보고",
      "어느 /dev/videoN 이 top(전체뷰) / wrist(손목) 인지 식별."]),
]


def banner(text):
    print("\n" + "=" * 66)
    print(f" {text}")
    print("=" * 66)


def main():
    missing = [c for c in ("lerobot-find-port", "lerobot-find-cameras")
               if not shutil.which(c)]
    if missing:
        print(f"[check] ERROR: {', '.join(missing)} 없음 — venv 활성화 확인:", file=sys.stderr)
        print("  source ~/smolvla/dgx/.arm_finetune/bin/activate", file=sys.stderr)
        sys.exit(1)

    banner("포트·카메라 인덱스 확인 — config/base_config.yaml 의 hardware 입력용")
    print("lerobot-find-port (follower·leader 2회) + lerobot-find-cameras 를 순차 실행합니다.")

    for idx, name, cmd, hints in STEPS:
        banner(f"[{idx}] {name}")
        for h in hints:
            print(f"  · {h}")
        try:
            input("\n  준비되면 Enter (이 단계 건너뛰려면 Ctrl-C)... ")
        except KeyboardInterrupt:
            print("\n  → 건너뜀.")
            continue
        try:
            subprocess.run(cmd, check=False)
        except KeyboardInterrupt:
            print("\n  → 중단됨, 다음 단계로.")

    banner("완료 — 다음 단계")
    print("위 출력에서 확인한 4개 값을 config/base_config.yaml 의 hardware 에 직접 입력:")
    print()
    print("  hardware:")
    print("    follower_port: /dev/ttyACMx     # [1/3] follower 결과")
    print("    leader_port:   /dev/ttyACMx     # [2/3] leader 결과")
    print("    camera_top_index:   N           # [3/3] top 카메라 /dev/videoN 의 정수 N")
    print("    camera_wrist_index: N           # [3/3] wrist 카메라 /dev/videoN 의 정수 N")
    print()
    print("그 후 검증: python run_record.py record --task 1 --episodes 10 --dry-run")


if __name__ == "__main__":
    main()
