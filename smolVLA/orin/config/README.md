# orin/config/ — 본 프로젝트 cached config

> 책임: SO-ARM 포트 / 카메라 인덱스·rotation·해상도 등 시연장 셋업 후 안정적인 환경 정보 cache. 운영 스크립트가 매번 발견·확인할 필요 없도록 영속화.

---

## 자산

| 파일 | 스키마 |
|---|---|
| `ports.json` | `{"follower_port": "/dev/ttyACM*", "leader_port": "/dev/ttyACM* \| null"}` |
| `cameras.json` | `{"<slot_name>": {"index": int, "rotation": int, "width": int, "height": int, "fps": int, "fourcc": str, "flip": bool}, ...}` |

### `ports.json` 예시

```json
{
  "follower_port": "/dev/ttyACM1",
  "leader_port": null
}
```

- `null` 은 미설정 (해당 자산이 현재 환경에 없음)
- 시연장 Orin 은 추론 전용이라 leader 미연결 — `leader_port: null` 정상

### `cameras.json` 예시

```json
{
  "top": {"index": 2, "rotation": -90, "width": 480, "height": 640, "fps": 30, "fourcc": "MJPG", "flip": false},
  "wrist": {"index": 0, "rotation": 0, "width": 640, "height": 480, "fps": 30, "fourcc": "MJPG", "flip": true}
}
```

- slot 이름은 본 프로젝트 컨벤션 (top, wrist) — 사전학습 분포 `svla_so100_pickplace` 와 일치
- `index` 는 OpenCV 디바이스 인덱스 (`/dev/video<N>` 의 N)
- `rotation`/`width`/`height`/`fps`/`fourcc` 는 수집/학습 base_config.yaml 의 카메라 설정과 정합 (`leftarm_v2_inference.py` 가 읽어 `OpenCVCameraConfig` 구성)
- `flip` 은 vertical flip 여부 (wrist 카메라 상하반전 보정용)

---

## 재생성 방법

```bash
# 환경 변동 (포트 재할당, 카메라 교체) 발생 시
lerobot-find-port
lerobot-find-cameras opencv
```

→ 발견된 값으로 본 디렉터리의 `ports.json` / `cameras.json` 수기 갱신.

---

## lerobot 표준 캘리브레이션 위치 (본 디렉터리 X)

`lerobot-calibrate` 가 SO-ARM follower / leader 의 모터 calibration JSON 을 자동 저장하는 표준 위치는:

```
~/.cache/huggingface/lerobot/calibration/<robot_id>.json
```

본 `orin/config/` 와 충돌하지 않도록 **lerobot 표준 그대로 사용** (복사·심볼릭 링크 X). 본 디렉터리는 본 프로젝트 자체 cached config 만 관리.

---

## git 추적 정책

- **본 README + ports.json + cameras.json 모두 git 추적** (사용자 환경 의존하나 시연장 셋업 후 안정적)

---

## 참고

- 추론 entry: [`orin/inference/README.md`](../inference/README.md)
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
