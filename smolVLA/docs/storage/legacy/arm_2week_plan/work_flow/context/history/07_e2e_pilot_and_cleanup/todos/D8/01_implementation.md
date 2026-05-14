# TODO-D8 — Implementation

> 작성: 2026-05-04 22:00 | task-executor | cycle: 1

## 목표

lerobot extras deepdiff 영구 fix 확인(II) + 카메라 메타 device 필터링(III) + 영상 viewer 강화(IV) 통합

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/precheck.py` | M | `_get_streamable_video_devices` 신규 + `_run_find_cameras_split` baseline 통합 + `_show_frame` ssh-file 안내 강화 |
| `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | M | D8 변경 이력 추가 (Part II 현황 + Part III·IV 변경 내용) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 — lerobot pyproject.toml Read-only 직접 인용 완료
- Coupled File Rule: `dgx/lerobot/` 미변경 (dgx/lerobot/ 미존재 — Option B 원칙 유지). `04_dgx_lerobot_diff.md` 동시 갱신
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/pyproject.toml` L110-114 (hardware extras), L140 (deepdiff-dep), L145 (feetech extras) 직접 인용
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py` line 308, 343-348 (VideoCapture.read 패턴) — `_get_streamable_video_devices` cv2 시도 패턴 기반

## Part II — setup_train_env.sh deepdiff 현황 확인

### lerobot pyproject.toml extras 직접 확인 결과

```toml
# docs/reference/lerobot/pyproject.toml line 110-114
hardware = [
    "lerobot[pynput-dep]",
    "lerobot[pyserial-dep]",
    "lerobot[deepdiff-dep]",        # deepdiff 포함
]
# line 140
deepdiff-dep = ["deepdiff>=7.0.1,<9.0.0"]
# line 145
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]
```

### 결론: setup_train_env.sh 변경 불필요

현재 `setup_train_env.sh` §3: `[smolvla,training,hardware,feetech]` extras 사용.
- `hardware` extras → `lerobot[deepdiff-dep]` → `deepdiff>=7.0.1,<9.0.0` transitive 포함
- `feetech` extras → `lerobot[deepdiff-dep]` → 동일
- §3-c 에도 `deepdiff>=7.0.1,<9.0.0` 명시 별도 설치 (D5 cycle 2, 중복이나 pip no-op)

**deepdiff-dep extras 별도 추가 불필요** — `[hardware,feetech]` 가 이미 transitive 포함.

reported deepdiff ImportError 원인 추정: D5 fix 이전 venv 미재설치 환경에서 발생. 새 설치 또는 재설치 시 `[hardware,feetech]` extras 로 deepdiff 자동 설치됨.

BACKLOG: `07 BACKLOG #3` — §3-c 의 deepdiff 개별 pip install 중복 라인 (§3 extras 통합 후 불필요) 정리를 차기 cleanup 사이클에서 처리.

## Part III — _get_streamable_video_devices 신규 + _run_find_cameras_split 통합

### 문제

Linux v4l2 는 카메라 1 개당 multiple device 를 노출:
- 예: USB 카메라 1개 → `/dev/video0` (main stream) + `/dev/video1` (metadata)
- 기존 `_get_video_devices()` 는 전체 glob → baseline 에 metadata device 포함
- wrist USB 분리 시 `/dev/video0` + `/dev/video1` 둘 다 사라짐 → 복수 device 사라짐 경고 발생

### 구현 — `_get_streamable_video_devices()`

```python
def _get_streamable_video_devices() -> list[str]:
    all_devs = sorted(glob.glob("/dev/video*"))
    # cv2 import 실패 시 fallback: 전체 목록 반환
    try:
        import cv2
    except ImportError:
        return all_devs

    streamable: list[str] = []
    for dev in all_devs:
        try:
            cap = cv2.VideoCapture(dev)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    streamable.append(dev)
            cap.release()
        except Exception:
            pass
    return streamable
```

레퍼런스 인용:
- `lerobot/cameras/opencv/camera_opencv.py` line 308: `camera = cv2.VideoCapture(target)`
- line 343-348: `ret, frame = self.videocapture.read()`
- line 309: `if camera.isOpened():`

### _run_find_cameras_split 통합

| 위치 | 변경 전 | 변경 후 |
|---|---|---|
| baseline 취득 | `set(_get_video_devices())` | `set(_get_streamable_video_devices())` |
| baseline_restored 취득 (wrist 재연결 후) | `set(_get_video_devices())` | `set(_get_streamable_video_devices())` |
| after_disconnect 취득 (분리 후) | `set(_get_video_devices())` | `set(_get_video_devices())` 유지 |

비교 원리: `baseline(streamable) - after_disconnect(all)` = streamable device 중 분리된 것 = 해당 카메라 main stream device.

### _get_video_devices() 보존

backward-compat 보존 — 변경 없음. 사전 스캔이 필요 없는 내부 after_disconnect 계산에서 계속 사용.

## Part IV — _show_frame ssh-file 안내 강화

### 변경 내용

ssh-file 모드 저장 후 출력 강화:

```
[precheck] 영상 저장됨 (wrist_left): /path/to/wrist_left_TIMESTAMP.jpg

         -- 영상 확인 방법 --
         VSCode remote-ssh 사용 중이면:
           좌측 Explorer 에서 아래 파일 클릭 → 자동 미리보기
           또는 터미널에서: code -r /path/to/wrist_left_TIMESTAMP.jpg
         ssh -Y dgx 사용 중 (X11 forwarding) 이면:
           ssh-x11 모드 선택 시 cv2.imshow 시도.
           X11 imshow 실패 시 libgtk2 설치 필요:
           sudo apt install libgtk2.0-dev pkg-config
         sftp / scp 로 로컬 전송 후 미리보기도 가능.

         (xdg-open 실행됨 — VSCode remote 미리보기 창 확인)
```

xdg-open 결과: `poll()` 로 성공/실패 명시 보고 (기존 silent 무시 → 명시 출력).

X11 fallback 안내 (ssh-x11 모드에서 cv2.error 발생 시):
- 기존: "ssh -Y dgx 재접속" 1 줄
- 변경 후: "1) ssh -Y dgx 재접속" + "2) libgtk2.0-dev 미설치" 2 원인 후보 명시

## 변경 내용 요약

**Part II**: `setup_train_env.sh` 변경 불필요 — D5 cycle 2 에서 `[hardware,feetech]` extras 추가 완료. `hardware` + `feetech` 가 각각 `lerobot[deepdiff-dep]` 을 transitive 포함 (lerobot pyproject.toml L110-114, L145 직접 확인). deepdiff-dep extras 별도 추가 불필요. `04_dgx_lerobot_diff.md` 에 현황 + 결론 기록.

**Part III**: `_get_streamable_video_devices()` 신규 추가 — cv2.VideoCapture read 성공 device 만 반환하여 v4l2 metadata device 제거. `_run_find_cameras_split` baseline 취득을 이 함수로 교체. 분리 후 after 상태는 전체 glob 유지하여 비교 정합성 보존. `_get_video_devices()` backward-compat 보존.

**Part IV**: `_show_frame` ssh-file 모드 안내 강화 — VSCode remote-ssh Explorer 클릭 + `code -r` 명령 안내 추가. xdg-open 결과 명시 보고. X11 fallback 메시지에 libgtk2 미설치 원인 후보 추가.

## code-tester 입장에서 검증 권장 사항

- 정적: `python3 -m py_compile dgx/interactive_cli/flows/precheck.py` PASS (확인 완료)
- lint: `ruff check dgx/interactive_cli/flows/precheck.py` PASS (확인 완료)
- diff 정합성:
  - `_get_streamable_video_devices` 함수 신규 존재 확인
  - `_run_find_cameras_split` 에서 `_get_streamable_video_devices()` 2회 호출 확인 (baseline, baseline_restored)
  - `_show_frame` ssh-file 분기에서 VSCode 안내 + xdg-open poll 결과 보고 확인
  - `04_dgx_lerobot_diff.md` D8 항목 추가 확인
- import smoke: `python3 -c "from dgx.interactive_cli.flows.precheck import _get_streamable_video_devices; print('OK')"` (DGX SSH)
- DOD 항목:
  - (II) `setup_train_env.sh` 갱신 X — DOD "사유 명시" + `04_dgx_lerobot_diff.md` 갱신으로 충족
  - (III) `_get_streamable_video_devices` 신규 + `_run_find_cameras_split` 통합 + cv2 시도 로직 정합 확인
  - (IV) `_show_frame` ssh-file 안내 강화 확인
  - py_compile + ruff PASS 확인 (완료)
