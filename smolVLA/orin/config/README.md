# orin/config/ — 본 프로젝트 cached config

> 책임: SO-ARM 포트 / 카메라 인덱스·flip 등 시연장 셋업 후 안정적인 환경 정보 cache. 운영 스크립트가 매번 발견·확인할 필요 없도록 영속화.
> 신설: 04_infra_setup TODO-O2 (2026-04-30)
> 갱신: `orin/tests/check_hardware.sh --mode first-time` (TODO-G1 구현 예정)

---

## 자산

| 파일 | 스키마 | 갱신 주체 |
|---|---|---|
| `ports.json` | `{"follower_port": "/dev/ttyACM*", "leader_port": "/dev/ttyACM*" \| null}` | first-time 모드 (TODO-G1) |
| `cameras.json` | `{"<slot_name>": {"index": int, "flip": bool}, ...}` | first-time 모드 (TODO-G1) |

### `ports.json` 예시

```json
{
  "follower_port": "/dev/ttyACM1",
  "leader_port": null
}
```

- `null` 은 미설정 (해당 자산이 현재 환경에 없음)
- 시연장 Orin 은 추론 전용이라 leader 미연결 — `leader_port: null` 정상

### `cameras.json` 예시 (03 prod 검증 결과 기준)

```json
{
  "top": {"index": 2, "flip": false},
  "wrist": {"index": 0, "flip": true}
}
```

- slot 이름은 본 프로젝트 컨벤션 (top, wrist) — 사전학습 분포 `svla_so100_pickplace` 와 일치
- `index` 는 OpenCV 디바이스 인덱스 (`/dev/video<N>` 의 N)
- `flip` 은 vertical flip 여부 (BACKLOG 03 #16 — wrist 카메라 상하반전 보정)

---

## 재생성 방법

```bash
# 환경 변동 (포트 재할당, 카메라 교체) 발생 시
bash orin/tests/check_hardware.sh --mode first-time --output-config orin/config/
```

(TODO-G1 구현 예정. 현재는 placeholder JSON 만 존재 — 사용자가 직접 수기 갱신 가능.)

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
- 다른 인스턴스 환경에서 충돌 가능 — 정책 명문화는 BACKLOG 04 #3 (낮음)

---

## 참고

- `docs/storage/07_orin_structure.md` §2 (config/ 컴포넌트 책임) + §4-5 (캘리브레이션 표준 위치)
- `docs/work_flow/specs/04_infra_setup.md` TODO-G1 (check_hardware.sh 구현)
- BACKLOG 04 #3 — git 추적 vs gitignore 정책 결정
