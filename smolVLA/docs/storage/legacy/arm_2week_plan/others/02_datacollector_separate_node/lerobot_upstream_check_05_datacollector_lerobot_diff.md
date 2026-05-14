# 05. datacollector/lerobot/ vs upstream 코드 변경 이력

> 목적: `lerobot/src/lerobot/` (upstream submodule) 대비 `datacollector/lerobot/` 의 차이를 누적 기록한다.
> upstream 기준 commit: `ba27aab79c731a6b503b2dbdd4c601e78e285048` (v0.5.1-42, 2026-04-22 동기화)
>
> 원칙: **옵션 B — 파일 변경 X**.
> DataCollector 는 데이터 수집 전용이므로 학습/추론/시뮬레이션 전용 코드는
> `pyproject.toml [project.scripts]` entrypoint 등록 해제만으로 비활성화.
> `datacollector/lerobot/` 내 파일 자체는 upstream 보존.

---

## 현재 상태 요약 (2026-05-01 초기 구성)

### upstream 대비 차이: 없음 (파일 레벨)

`datacollector/lerobot/` 은 upstream `lerobot/src/lerobot/` 과 파일 레벨에서 동일하다.
DataCollector 는 x86_64 Python 3.12 환경이므로 Orin 의 Python 3.10 호환 패치도 불필요.

### 비활성화 방식: pyproject.toml entrypoint 만

DataCollector 에서 사용하지 않는 기능은 `datacollector/pyproject.toml [project.scripts]` 에 entrypoint 를 미등록하는 것으로 비활성화.

| entrypoint | DataCollector 포함 여부 | 이유 |
|---|---|---|
| `lerobot-record` | ✅ | 핵심 기능 — 데이터 수집 |
| `lerobot-teleoperate` | ✅ | 핵심 기능 — SO-ARM 텔레오퍼레이션 |
| `lerobot-calibrate` | ✅ | SO-ARM 캘리브레이션 |
| `lerobot-find-cameras` | ✅ | 카메라 인덱스 발견 |
| `lerobot-find-port` | ✅ | SO-ARM 포트 발견 |
| `lerobot-find-joint-limits` | ✅ | 관절 각도 한계 발견 |
| `lerobot-replay` | ✅ | 에피소드 재생 |
| `lerobot-setup-motors` | ✅ | 모터 초기 설정 |
| `lerobot-info` | ✅ | 환경 정보 확인 |
| `lerobot-eval` | ❌ | DataCollector 는 추론·평가 X (Orin 책임) |
| `lerobot-train` | ❌ | DataCollector 는 학습 X (DGX 책임) |
| 기타 시각화 유틸 | ❌ | 수집 전용 노드에 불필요 |

### orin/lerobot/ 과의 차이

`datacollector/lerobot/` 은 `orin/lerobot/` 과 달리 Python 3.10 호환 패치가 없다.
DataCollector 는 x86_64 Python 3.12 이므로 upstream 그대로 사용.

| 패치 항목 | orin/lerobot/ | datacollector/lerobot/ |
|---|---|---|
| Python 3.12 `type` alias 문법 → `Union[]` | 패치 적용 | 패치 불필요 (Python 3.12) |
| Python 3.12 generic 함수 → TypeVar | 패치 적용 | 패치 불필요 (Python 3.12) |
| `hil_processor` import 제거 | 제거 | 파일 변경 X (옵션 B — 단 entrypoint 미등록) |
| smolvla 외 policy import 제거 | 제거 | 파일 변경 X (옵션 B — smolvla extras 미정의) |

---

## 변경 이력

### [2026-05-01] 초기 구성 — 04_infra_setup TODO-D2

**대상:** `datacollector/` 신규 구성 (DataCollector 전용 디렉터리)

**변경 내용:**

- `datacollector/pyproject.toml` 신규 작성 — `record + hardware + feetech` extras 정의, `smolvla + training` 미정의, entrypoint 9개 등록 (`eval + train` 미등록)
- `datacollector/lerobot/` — 옵션 B 원칙: 파일 변경 X. upstream src 복사 또는 symlink (setup_env.sh §0-b 처리)
- coupled file 신규 작성: 본 문서

**변경 이유:**

04_infra_setup 마일스톤 4-노드 아키텍처 도입. DataCollector 는 데이터 수집 전용.
Orin 의 smolvla·추론 모듈 불필요. DGX 의 학습 모듈 불필요.
→ entrypoint 등록 해제로 책임 범위 명확화.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| `lerobot-eval` CLI 호출 | ❌ (DataCollector 에서 호출 안 됨) |
| `lerobot-train` CLI 호출 | ❌ (DataCollector 에서 호출 안 됨) |
| `lerobot-record` / `lerobot-teleoperate` 등 9개 CLI | ✅ 정상 동작 |
| upstream 동기화 부담 | 낮음 — 파일 변경 없어 동기화 시 그대로 적용 가능 |

**잔여 리스크:**

- upstream 동기화 시 entrypoint 정리가 덮어씌워질 수 있음 (Orin 과 동일 리스크 — BACKLOG 04 #1 참조)
- `datacollector/lerobot/` 실체 (symlink vs 실제 파일 복사) 는 setup_env.sh §0-b 에서 처리. TODO-D3 prod-test 시 확인 필요.

---

## upstream 동기화 시 재확인 항목

- [ ] `[project.scripts]` 변경 → 새 스크립트 추가 시 DataCollector 에 필요한지 판단 후 entrypoint 추가
- [ ] 신규 패키지 upstream 추가 → `record + hardware + feetech` extras 범위에 포함되는지 확인
- [ ] Python 버전 제약 변경 → `requires-python` 상한 확인 (DataCollector: `>=3.12`)
