# orin/config/ — Orin 운영 설정

> 책임: 디바이스 매핑 (udev rule) + 카메라 부가 설정 cache. 운영 스크립트가 진입 시 의존하는 영속 자산.

---

## 자산

| 파일 / 디렉터리 | 스키마·역할 |
|---|---|
| `udev/99-hylion.rules` | SO-ARM 좌/우 + 카메라 top/wrist 의 시리얼 기반 영속 심볼릭 링크 정의 (`/dev/so_arm_left`, `/dev/so_arm_right`, `/dev/cam_top`, `/dev/cam_wrist`) |
| `cameras.json` | 카메라 부가 파라미터 (rotation/width/height/fps/fourcc/flip). device path 는 udev 가 담당 — 본 파일에 인덱스 X |
| `README.md` | 본 문서 |

### `cameras.json` 스키마

```json
{
  "top":   {"rotation": -90, "width": 480, "height": 640, "fps": 30, "fourcc": "MJPG", "flip": false},
  "wrist": {"rotation":   0, "width": 640, "height": 480, "fps": 30, "fourcc": "MJPG", "flip": false}
}
```

- slot 이름: `top`, `wrist` — 본 프로젝트 컨벤션 (사전학습 분포 `svla_so100_pickplace` 와 일치). 코드가 키로부터 `/dev/cam_<key>` 도출
- `rotation`/`width`/`height`/`fps`/`fourcc` 는 DGX 수집 + 학습 base_config.yaml 의 카메라 설정과 정합 (`leftarm_v2_inference.py` 가 읽어 `OpenCVCameraConfig` 구성)
- `flip` = vertical flip 여부 (wrist 카메라 상하반전 보정용)

### `udev/99-hylion.rules` 스키마

시리얼 단독 매칭. 2026-05-24 ssh 실측으로 시리얼 unique 확인.

| 심볼릭 링크 | 매칭 키 | 모델 |
|---|---|---|
| `/dev/cam_top` | `0bda:0565` + `serial=200901010001` + `ATTR{index}==0` | YJX-C5 (Realtek 보드캠) |
| `/dev/cam_wrist` | `0c45:6367` + `serial=SN0001` + `ATTR{index}==0` | Innomaker U20CAM-720P (Microdia) |
| `/dev/so_arm_left` | `1a86:55d3` + `serial=5AE6056701` | SO-ARM Feetech (WCH CH343) |
| `/dev/so_arm_right` | `1a86:55d3` + `serial=5AE6082773` | SO-ARM Feetech (WCH CH343) |

---

## udev rule 설치 (Orin)

```bash
sudo install -o root -g root -m 644 \
  ~/smolvla/orin/config/udev/99-hylion.rules \
  /etc/udev/rules.d/99-hylion.rules
sudo udevadm control --reload
sudo udevadm trigger

# 검증
ls -la /dev/cam_top /dev/cam_wrist /dev/so_arm_left /dev/so_arm_right
```

→ 4개 링크 정상 생성되면 운영 wrapper 진입 시 `validate_devices()` 가 자동 확인.

---

## 디바이스 추가·교체 시

1. ssh orin 에서 `udevadm info -q property -n /dev/<new_dev>` 로 `ID_VENDOR_ID` / `ID_MODEL_ID` / `ID_SERIAL_SHORT` 추출
2. `udev/99-hylion.rules` 에 새 SUBSYSTEM 규칙 추가 (동일 모델일 경우 시리얼 충돌 확인 필수 — Innomaker 류는 동일 SN 양산 가능)
3. 위 설치 명령 재실행
4. 동일 모델 추가 시 시리얼 매칭 불가하면 USB path (`KERNELS=="1-2.2.X"`) 로 강제

---

## lerobot 표준 캘리브레이션 위치 (본 디렉터리 X)

`lerobot-calibrate` 가 SO-ARM follower / leader 의 모터 calibration JSON 을 자동 저장하는 표준 위치는:

```
~/.cache/huggingface/lerobot/calibration/<robot_id>.json
```

본 `orin/config/` 와 충돌하지 않도록 **lerobot 표준 그대로 사용** (복사·심볼릭 링크 X). 본 디렉터리는 본 프로젝트 자체 cached config 만 관리.

---

## git 추적 정책

- 본 README + `cameras.json` + `udev/99-hylion.rules` 모두 git 추적 (사용자 환경 의존하나 시연장 셋업 후 안정적)

---

## 참고

- 추론 entry: [`orin/inference/README.md`](../inference/README.md)
- 진입 wrapper: [`orin/scripts/run_inference_leftarm_v2.sh`](../scripts/run_inference_leftarm_v2.sh) (`validate_devices()` 함수)
- Legacy 발견·캐시 게이트: [`orin/docs/legacy/README.md`](../docs/legacy/README.md) §1-3
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
