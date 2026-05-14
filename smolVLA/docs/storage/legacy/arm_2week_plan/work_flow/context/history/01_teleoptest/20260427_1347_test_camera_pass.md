# Current Test Target
<!-- /handoff-test 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-27 13:16 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 05

## 테스트 목표

OV5648 카메라 2대 인식 및 스트림 확인.  
Orin에서 카메라 2대가 `/dev/video*`로 인식되고 이미지 스트림이 정상 출력되는지 확인.  
화각(68° vs 72°)·포커스(Fixed vs Auto) 표기 불일치를 실물 확인으로 확정한다.

## DOD (완료 조건)

1. OV5648 카메라 2대가 `/dev/video*`로 인식됨
2. 각 장치에서 이미지 스트림이 정상 출력됨
3. 화각이 68°인지 72°/120°인지 육안 또는 스트림으로 확정됨
4. Fixed Focus인지 Auto Focus인지 확정됨

## 환경

Orin JetPack 6.2.2 | Python 3.10  
하드웨어: OV5648 USB 카메라 2대 Orin 연결 필요  
(SO-ARM 보드 2개와 동시 연결 시 USB 허브 필요할 수 있음)

## ⚠️ 사전 확인

- `/dev/video*` 번호는 연결 순서에 따라 바뀔 수 있음 — Codex #3(`v4l2-ctl --list-devices`) 결과로 실제 번호 확인 후 #4·#5 실행
- USB 포트 수 부족 시 허브 사용

## Codex 검증 (비대화형)
<!-- Codex가 SSH 비대화형으로 실행하고 결과 컬럼을 채운다 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `ssh orin echo ok` | `ok` 출력 | PASS: `ok` | SSH 접속 확인 |
| 2 | `ssh orin "ls /dev/video* 2>/dev/null || echo 'no video devices'"` | `/dev/video0`, `/dev/video1` 등 2개 이상 출력 | PASS: `/dev/video0`, `/dev/video1`, `/dev/video2`, `/dev/video3` | 카메라 장치 4개 노드 인식됨 |
| 3 | `ssh orin "v4l2-ctl --list-devices 2>/dev/null || echo 'v4l2-ctl not found'"` | 카메라 2대의 장치명·드라이버 출력 | FAIL: `v4l2-ctl not found` | `v4l2-ctl` 미설치로 실제 `/dev/video*` 번호 확정 불가 |
| 4 | `ssh orin "v4l2-ctl --device=/dev/video0 --list-formats-ext 2>/dev/null"` | 지원 포맷·해상도 목록 출력 | FAIL: 출력 없음, exit 127 | #3에서 번호 확정 불가하여 기본 `/dev/video0`로 실행; `v4l2-ctl` 미설치 |
| 5 | `ssh orin "v4l2-ctl --device=/dev/video2 --list-formats-ext 2>/dev/null"` | 지원 포맷·해상도 목록 출력 | FAIL: 출력 없음, exit 127 | #3에서 번호 확정 불가하여 기본 `/dev/video2`로 실행; `v4l2-ctl` 미설치 |

## 개발자 직접 검증 (대화형)
<!-- 개발자가 Orin Remote SSH 터미널에서 실행하고 결과를 기록한다 -->
<!-- 화각·포커스 육안 확인은 캡처 이미지를 devPC로 복사하거나 Remote 터미널에서 확인 -->

| # | 단계 | 기대 결과 | 결과 | 비고 |
|---|---|---|---|---|
| 1 | `python3 -c "import cv2; cap=cv2.VideoCapture(0); ret,f=cap.read(); cv2.imwrite('/tmp/cam0.jpg',f); cap.release(); print(ret)"` | `True` 출력, `/tmp/cam0.jpg` 생성 | PASS(대체 확인): `/dev/video0` 실시간 스트리밍 정상 출력 확인 | 파일 캡처 대신 Orin 화면 실시간 스트리밍으로 확인 |
| 2 | 두 번째 카메라에 동일 실행 (`VideoCapture(2)` 등) | `True` 출력, `/tmp/cam1.jpg` 생성 | PASS(대체 확인): `/dev/video2` 실시간 스트리밍 정상 출력 확인 | 파일 캡처 대신 Orin 화면 실시간 스트리밍으로 확인 |
| 3 | `scp orin:/tmp/cam*.jpg .` (devPC에서 실행) 후 이미지 열기 | 이미지가 정상 출력됨 | PASS(대체 확인): Orin 화면에서 카메라 2대 영상 확인 | `DISPLAY=:1`, `gst-launch-1.0 v4l2src device=/dev/videoN do-timestamp=true ! queue leaky=downstream max-size-buffers=1 ! videoconvert ! ximagesink sync=false` 사용. 파일 복사 확인 대신 실시간 스트리밍으로 확인 |
| 4 | **[육안]** 이미지 화각 확인 — 좁으면 68°·72° 추정, 광각이면 120° | 화각 확정 | PASS: 동일 모델 기준 50cm 거리에서 화면 가로축 끝-끝 약 50cm 확인 → 수평 FOV 환산 약 53° | 120° 광각은 아님. 68° 표기는 대각 FOV일 가능성 있음 |
| 5 | **[육안]** 카메라를 가까이/멀리 이동하며 초점 자동 조정 여부 확인 | 자동 조정 → Auto Focus, 고정 → Fixed Focus | PASS: Auto Focus 가능 확인 | 동일 모델 기준 포커스 사양 Auto Focus로 기록 |
| 6 | 확인된 화각·포커스 사양을 여기에 기록 | — | PASS: 카메라 2대 모두 실시간 스트리밍 정상. 동일 모델 기준 120° 광각 아님. 실측 수평 FOV 약 53°(50cm 거리에서 가로 약 50cm). 68° 표기는 대각 FOV 가능성 있음. Auto Focus 가능 확인 | TODO-05 DOD 충족. Codex 비대화형 포맷 조회는 `v4l2-ctl` 미설치로 실패했으나, 개발자 실시간 스트리밍 검증으로 동작 확인 완료 |
