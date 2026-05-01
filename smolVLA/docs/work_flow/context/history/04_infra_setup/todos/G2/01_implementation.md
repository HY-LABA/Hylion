# TODO-G2 — check_hardware.sh prod 검증 + hil_inference.py 게이트 통합

> 작성: 2026-05-01 15:05 | task-executor | cycle: 1
> 갱신: 2026-05-01 | task-executor | cycle: 2 (MINOR_REVISIONS 반영)

## 목표

TODO-G1 산출물(check_hardware.sh)의 Orin prod 검증 시나리오 정의 + hil_inference.py 에
`--gate-json` 옵션 추가 (게이트 결과 cache JSON 으로 미지정 CLI 인자 자동 채우기).

---

## 사전 점검 결과

### check_hardware.sh JSON output schema 추출

`--output-json` 플래그가 생성하는 파일 형식 (`check_hardware.sh finalize_output` 함수):

```json
{
  "mode": "first-time|resume",
  "steps": {
    "venv":       {"status": "PASS|FAIL", "detail": "..."},
    "cuda":       {"status": "PASS|FAIL", "detail": "..."},
    "soarm_port": {"status": "PASS|FAIL", "detail": "..."},
    "cameras":    {"status": "PASS|FAIL", "detail": "..."}
  },
  "summary": {"pass": N, "fail": N, "exit_code": 0|1}
}
```

이 JSON 에는 follower_port·camera index 값이 직접 들어 있지 않고 `detail` 문자열 안에만 포함된다.
따라서 `--gate-json` 은 `check_hardware.sh --output-json` 결과 파일이 아닌
`orin/config/ports.json` / `cameras.json` cache 파일을 지정하는 방식을 채택했다.

### orin/config/ cache 파일 schema

**ports.json** (check_hardware.sh step_soarm_port 갱신):
```json
{"follower_port": "/dev/ttyACM0|null", "leader_port": "/dev/ttyACM1|null"}
```

**cameras.json** (check_hardware.sh step_cameras 갱신):
```json
{
  "top":   {"index": "/dev/video0|0|null", "flip": false},
  "wrist": {"index": "/dev/video2|2|null", "flip": true}
}
```

**schema 일관성 판정**: hil_inference.py 와 check_hardware.sh 간 JSON schema 불일치 없음.
`--gate-json` 은 `check_hardware.sh --output-json` 결과가 아닌 `orin/config/` cache 를 대상으로 함 (명확히 구분).

### hil_inference.py 기존 argparse 분석

| 인자 | 타입 | 기본값 | gate JSON 로 채울 대상 |
|---|---|---|---|
| `--follower-port` | str | None (이전: required) | ports.json.follower_port |
| `--cameras` | dict | top:0,wrist:1 | cameras.json.top.index + wrist.index |
| `--flip-cameras` | set | empty | cameras.json.top.flip + wrist.flip |
| `--mode` / `--follower-id` / `--n-action-steps` / `--max-steps` / `--output-json` | - | - | gate 대상 외 |

### BACKLOG 03 #15·#16 해소 매핑

| BACKLOG | 해소 경로 |
|---|---|
| 03 #15 카메라 인덱스 사전 발견 | G1: check_hardware.sh 가 cameras.json 에 index 저장. G2: hil_inference.py `--gate-json` 이 그 값 로드 → `--cameras` 자동 채움 |
| 03 #16 wrist flip | G1: cameras.json 에 wrist.flip 저장. G2: `--gate-json` 이 `--flip-cameras wrist` 자동 채움 |

---

## 산출물

### 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/inference/hil_inference.py` | M | `--gate-json` 옵션 추가 + `load_gate_config`·`apply_gate_config` 헬퍼 2개 추가 (~75 줄 순 추가) |

### 새 `--gate-json` 옵션 동작 명세

**인자:**
```
--gate-json <path>
```
- `<path>` 가 디렉터리이면: `<path>/ports.json` + `<path>/cameras.json` 로드
- `<path>` 가 파일이면: 그 파일의 부모 디렉터리에서 `ports.json` + `cameras.json` 로드

**채움 규칙 (CLI 직접 지정이 항상 우선):**

| 조건 | 적용 동작 |
|---|---|
| `--follower-port` 미지정 (`None`) + `ports.json.follower_port` 비어 있지 않음 | `--follower-port` 자동 채움 |
| `--cameras` 가 기본값 `top:0,wrist:1` + `cameras.json` 에 non-null index 있음 | `--cameras` 자동 채움 |
| `--flip-cameras` 가 빈 set + `cameras.json.*.flip == true` 항목 있음 | `--flip-cameras` 자동 채움 |

**cameras.json index 타입 처리:**
- int 변환 가능 → int (`OpenCVCameraConfig.index_or_path` 가 int 허용)
- 변환 불가 (예: `/dev/video0`) → str 그대로 (`index_or_path` 가 str 도 허용)

**하위 호환:**
- `--gate-json` 미지정 시 기존 동작 100% 동일
- `--follower-port` 를 직접 지정하면 gate JSON 값 무시
- `--cameras` 를 기본값 아닌 값으로 직접 지정하면 gate JSON 값 무시
- `--flip-cameras` 를 직접 지정하면 gate JSON 값 무시

**edge case:**
- `--cameras top:0,wrist:1` 을 CLI 에서 직접 지정해도 기본값과 동일하므로 gate 값에 덮어씌워진다.
  사용자가 기본값과 동일한 인덱스를 강제하려면 `--gate-json` 을 생략해야 한다.
  (이 한계는 `--cameras` 기본값 구분 불가 문제로, 향후 `--no-gate-cameras` 플래그 추가로 해소 가능 — BACKLOG 후보)

**신규 추가 import:**
- `from pathlib import Path` — 기존 없던 stdlib import 1개 추가

---

## 검증 시나리오 정의 (prod-test-runner 입력)

### 자율 가능 (prod-test-runner SSH)

prod-test-runner 가 `orin` SSH 에서 순서대로 실행:

1. **devPC 배포**:
   ```bash
   bash scripts/deploy_orin.sh
   ```
   - 변경 파일: `orin/inference/hil_inference.py` 1개 (Category B 외)
   - 자율 배포 가능 조건 충족

2. **check_hardware.sh 문법 검증 (ANOMALIES #1 SKILL_GAP 해소)**:
   ```bash
   ssh orin "bash -n ~/smolvla/orin/tests/check_hardware.sh"
   ```
   - G1 code-tester 가 sandbox 차단으로 미검증 → G2 에서 Orin SSH 직접 해소
   - 성공 기준: exit=0, 출력 없음

3. **check_hardware.sh --help**:
   ```bash
   ssh orin "bash ~/smolvla/orin/tests/check_hardware.sh --help"
   ```
   - 성공 기준: exit=2 (usage 출력 후 종료), 인자 목록 (--mode / --config / --quiet / --output-json) 출력 확인

4. **check_hardware.sh resume 비대화형 실행**:
   ```bash
   ssh orin "bash ~/smolvla/orin/tests/check_hardware.sh --mode resume --quiet --output-json /tmp/hw_gate.json"
   ```
   - 현시점 ports.json·cameras.json 은 null → soarm_port PASS (null 건너뜀), cameras FAIL 예상
   - 성공 기준: 스크립트가 exit 0|1 으로 종료 (크래시 없음), `/tmp/hw_gate.json` 생성, JSON 파싱 가능

5. **hil_inference.py --help (새 --gate-json 옵션 확인)**:
   ```bash
   ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/inference/hil_inference.py --help"
   ```
   - 성공 기준: exit=0, `--gate-json` 옵션 help 텍스트 출력 확인

6. **hil_inference.py --gate-json (auto-arg 로딩 검증 — placeholder null 상태)**:
   ```bash
   ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/inference/hil_inference.py --gate-json ~/smolvla/orin/config/ports.json --mode dry-run --output-json /tmp/test_action.json 2>&1 | head -20"
   ```
   - 현재 ports.json.follower_port = null → `[gate] ports.json.follower_port = null` 경고 출력 후
     `--follower-port 는 필수` 오류 (exit≠0) — 이것이 **정상 동작**
   - 성공 기준: `[gate]` 접두어 로그 출력 확인 (`gate-json` 로딩 코드 실행 확인)

### 사용자 실물 필요 (verification_queue 추가)

prod-test-runner 가 아래 3건을 verification_queue.md 에 추가:

1. **first-time 모드 (카메라 2대 + SO-ARM follower 연결 필요)**:
   ```bash
   bash ~/smolvla/orin/tests/check_hardware.sh --mode first-time
   ```
   - Orin 콘솔에서 직접 실행 (X11 없이 카메라 인덱스 확인, wrist flip 여부 사용자 응답)
   - 성공 기준: 4단계 모두 PASS, ports.json·cameras.json 에 실 값 저장

2. **resume 모드 (first-time 완료 후)**:
   ```bash
   bash ~/smolvla/orin/tests/check_hardware.sh --mode resume --quiet --output-json /tmp/hw_resume.json
   ```
   - 성공 기준: exit=0, 4단계 모두 PASS, JSON 파싱 가능

3. **hil_inference.py --gate-json 실 동작 (first-time 완료 후, SO-ARM + 카메라 연결 상태)**:
   ```bash
   source ~/smolvla/orin/.hylion_arm/bin/activate
   python ~/smolvla/orin/inference/hil_inference.py \
     --gate-json ~/smolvla/orin/config/ports.json \
     --mode dry-run --output-json /tmp/hil_gate_test.json --max-steps 5
   ```
   - 성공 기준: `[gate]` 로그에서 follower_port·cameras·flip_cameras 자동 채워짐 확인,
     5 step dry-run 완료, action JSON 저장

---

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경.
- CLAUDE.md Hard Constraints Category B: `orin/lerobot/` 미변경, `pyproject.toml` 미변경. `orin/inference/hil_inference.py` 는 Category B 외 — 자동 재시도 가능 영역.
- Coupled File Rules: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요. `pyproject.toml` 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요. stdlib `pathlib.Path` 추가는 pyproject 의존성 변경 없음.
- 레퍼런스 활용: 기존 `hil_inference.py` 의 argparse 패턴 그대로 유지 (인자 선언 방식, parse 후 검증 패턴). 신규 `load_gate_config` / `apply_gate_config` 는 lerobot 레퍼런스에 동일 구현 없는 프로젝트 특화 로직 → SKILL_GAP 보고 대상이지만, 기존 hil_inference.py argparse 패턴 확장이고 TODO 에 명시적으로 정의된 기능이므로 orchestrator 사전 승인된 신규 자산으로 판단.
- 03 산출물 회귀 X 원칙: `--gate-json` 미지정 시 기존 동작 100% 동일. `--follower-port` 는 기존 required → default=None + 사후 검증으로 변경했으나 외부 동작 동일.

---

## 변경 내용 요약

`orin/inference/hil_inference.py` 에 `--gate-json <path>` 인자를 추가했다. 이 인자는 `check_hardware.sh` 가 `first-time` 모드에서 생성하는 `orin/config/ports.json` 과 `cameras.json` cache 파일을 읽어서 미지정 CLI 인자 (`--follower-port`, `--cameras`, `--flip-cameras`) 를 자동으로 채운다. CLI 에 직접 인자를 지정한 경우 항상 그쪽이 우선이므로 하위 호환이 보장된다.

신규 헬퍼 함수 2개: `load_gate_config(path)` 는 경로가 디렉터리이면 그 안에서, 파일이면 그 부모 디렉터리에서 `ports.json` 과 `cameras.json` 을 로드한다. `apply_gate_config(args, ports_data, cameras_data, parser)` 는 로드된 데이터로 `args` 를 채운다. 두 함수 모두 JSON 파싱 실패나 파일 미존재를 graceful 하게 처리한다 (`stderr` 경고 출력 후 계속 진행).

BACKLOG 03 #15 (카메라 인덱스 사전 발견) 와 #16 (wrist flip) 이 코드 수준에서 완전히 해소된다. `check_hardware.sh first-time` 후 생성된 `cameras.json` 의 `top.index`, `wrist.index`, `wrist.flip` 값이 `--gate-json` 를 통해 hil_inference.py 의 `--cameras` / `--flip-cameras` 로 자동 전달된다.

---

## 잔여 리스크 / SKILL_GAP

- **SKILL_GAP #1 (G1, ANOMALIES.md #1)** — `bash -n` sandbox 차단 → G2 prod-test-runner 가 Orin SSH 에서 직접 실행하여 해소. prod-test-runner 가 ANOMALIES.md 갱신 의무 (결과 기록).
- **cameras.json index 타입 불일치**: `check_hardware.sh` 는 `str(cams[0]['id'])` 로 문자열 index 를 저장하지만, `parse_camera_arg` 는 int 변환을 기대한다. `apply_gate_config` 에서 `_to_idx()` 로 int/str 모두 처리하도록 수정. `OpenCVCameraConfig.index_or_path` 가 int|str 모두 허용하므로 하류에서 문제 없음.
- **--cameras 기본값 덮어쓰기 edge case**: CLI 에서 `top:0,wrist:1` 을 명시적으로 지정해도 기본값과 동일하여 gate 값으로 덮어씌워진다. 현실적으로 cameras.json 에 실 값이 채워져 있으면 항상 gate 값이 더 정확하므로 실용적 문제 없음. 향후 `--no-gate-cameras` 플래그로 명시적 비활성화 지원 가능 (BACKLOG 후보).

---

## 검증 필요 (다음 단계)

- **code-tester**:
  - `python -m py_compile orin/inference/hil_inference.py` — 컴파일 오류 없음
  - `--help` 출력에 `--gate-json` 옵션 포함 확인
  - `--gate-json` 미지정 시 기존 동작 (argparse 동작) 하위 호환 확인
  - `load_gate_config` 경로 처리 로직 (디렉터리 vs 파일) 코드 리뷰
  - `apply_gate_config` 채움 조건 (None, 기본값, 빈 set) 코드 리뷰
  - `_to_idx` int/str 변환 로직 리뷰
  - 기존 argparse 인자 (`--mode`, `--follower-id`, 등) 변경 없음 확인

- **prod-test-runner (자율 6단계 SSH + 사용자 3건 verification_queue)**:
  - 자율 단계 1~6 순서대로 실행
  - ANOMALIES.md #1 (`bash -n` SKILL_GAP) 해소 여부 결과 기록
  - 사용자 실물 3건 verification_queue.md 추가

---

## cycle 2 수정 (2026-05-01)

> MINOR_REVISIONS 3건 반영. 재검증 없이 prod-test-runner 진입.

### Recommended #1 해소 — _to_idx() Path 타입

- `str(v)` fallback → `Path(v)` 로 교체
- 근거: `OpenCVCameraConfig.index_or_path: int | Path` (orin/lerobot/cameras/opencv/configuration_opencv.py line 61) — str 불허
- `from pathlib import Path` 는 이미 line 37 에서 import 돼 있으므로 추가 import 불필요
- 검증: `grep -n "_to_idx" orin/inference/hil_inference.py` — `return Path(v)` 확인

### Recommended #2 해소 — dead catch 제거

- `apply_gate_config` 내 외부 `try / except Exception as e` 블록 제거
- `_to_idx()` 내부의 `except (ValueError, TypeError)` 만으로 충분 — 외부 catch 는 실질적으로 도달 불가(dead)였음
- 코드 -4줄 순 감소

### Recommended #3 해소 — prod-test 시나리오 6번 보강

- 자율 시나리오 6번 명령에 `--follower-port /dev/ttyACM0 --cameras top:0,wrist:1` 명시 추가
- 이유: `--gate-json` 만 지정 시 ports.json.follower_port=null → `parser.error("--follower-port 필수")` 가
  `[gate]` 로그 출력보다 먼저 exit 하면 gate 코드 경로 확인 불가
- `--follower-port` 를 명시하면 gate 로직 통과 → `[gate] cameras ← ...` 로그 확인 가능
- 보강된 시나리오 6번:
  ```bash
  ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && \
    python ~/smolvla/orin/inference/hil_inference.py \
      --gate-json ~/smolvla/orin/config/ports.json \
      --follower-port /dev/ttyACM0 \
      --cameras top:0,wrist:1 \
      2>&1 | head -20"
  ```
  - `--follower-port` 명시로 parser.error 회피
  - cameras.json placeholder null 값 → `[gate]` 경고 메시지 출력 확인
  - 성공 기준: `[gate]` 접두어 로그 출력 (gate-json 로딩 코드 실행 확인), 이후 모델 로드 또는 카메라 연결 실패로 종료 (정상)

### 다음 단계

- cycle 2 종료 → G2 prod-test-runner 진입
- prod-test-runner: 자율 6단계 (보강된 시나리오 6번 포함) + verification_queue 3건 추가
