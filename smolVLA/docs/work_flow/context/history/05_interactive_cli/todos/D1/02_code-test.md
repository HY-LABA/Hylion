# TODO-D1 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건. Recommended 개선 사항: 2건.

---

## 단위 테스트 결과

```
해당 없음 (study todo — 코드 구현 없음, 단위 테스트 대상 파일 없음)
```

---

## Lint·Type 결과

```
해당 없음 (docs/storage/ 신규 문서 파일만 생성, Python 소스 없음)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. datacollector flow 2~7 단계 구체 동작 정의 | ✅ | §1~§5 전 구간 정의 완료 |
| 2. 5단계 학습 종류 옵션 후보 ≤5개 작성 | ✅ | 정확히 5개 후보 도출 |
| 3. 6단계 lerobot-record draccus 인자 매핑 결정 | ✅ | §4 고정 인자 + 사용자 입력 + 5단계 매핑 표 완비 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `15_datacollector_cli_flow.md` §4 고정 인자 표, "결정 근거" 열 | `--robot.type=so101_follower` 의 인용 라인을 `run_teleoperate.sh line 29` 로 기술했으나, 실제 파일에서 `--robot.type=so101_follower` 는 `calibrate_follower()` 함수 내 line 27에 위치. line 29 는 `--robot.id` 행. 다음 사이클 기회 시 line 27 로 정정 권장 (논리 오류 없음, 참조 라인만 부정확). |
| 2 | `15_datacollector_cli_flow.md` §5 flow 7 분기 2 코드 주석, "line 6: 실행 위치: devPC" 인용 | `sync_dataset_collector_to_dgx.sh` line 6 은 `# 사용:` 주석 행. "실행 위치: devPC (어디서든)" 텍스트는 실제 line 4에 있음. 01_implementation.md 및 §5 본문에서 "line 6" 으로 인용했으나 line 4 가 정확한 라인. 다음 사이클 기회 시 정정 권장 (실행 위치 자체는 정확히 기술됨). |

---

## 레퍼런스 정합성 검증 상세

### lerobot_record.py DatasetRecordConfig 시그니처

실제 파일 (`docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py`) 과 §4 인용 대조:

| 필드 | 문서 인용 라인 | 실제 라인 | 값·타입 일치 |
|---|---|---|---|
| `repo_id: str` | line 163 | line 163 | ✅ |
| `single_task: str` | line 165 | line 165 | ✅ |
| `root: str | Path | None = None` | line 167 | line 167 | ✅ |
| `fps: int = 30` | line 169 | line 169 | ✅ |
| `num_episodes: int = 50` | line 175 | line 175 | ✅ |
| `push_to_hub: bool = True` | line 179 | line 179 | ✅ |
| `streaming_encoding: bool = False` | line 202 | line 202 | ✅ |
| `encoder_threads: int | None = None` | line 208 | line 208 | ✅ |
| `vcodec: str = "libsvtav1"` | line 199 | line 199 | ✅ |
| `__post_init__` validation | line 212~214 | line 212~214 | ✅ |
| `RecordConfig` class | line 217~258 | line 217~258 | ✅ |

### run_teleoperate.sh 상수값

| 상수 | 문서 인용 | 실제 값·라인 | 일치 |
|---|---|---|---|
| `FOLLOWER_PORT="/dev/ttyACM1"` | line 19 | line 19 | ✅ |
| `LEADER_PORT="/dev/ttyACM0"` | line 20 | line 20 | ✅ |
| `FOLLOWER_ID="my_awesome_follower_arm"` | line 21 | line 21 | ✅ |
| `LEADER_ID="my_awesome_leader_arm"` | line 22 | line 22 | ✅ |
| `--robot.type=so101_follower` | line 29 인용 | 실제 line 27 | ⚠️ Recommended #1 |
| `--teleop.type=so101_leader` | line 35 | line 35 (`calibrate_leader`) | ✅ |
| `all` case 순서 | line 70~74 | line 70~75 (case: 70, 내용: 71~74) | ✅ 허용 범위 |

### push_dataset_hub.sh

| 검증 항목 | 문서 기술 | 실제 파일 | 일치 |
|---|---|---|---|
| HF 인증 체크 로직 | line 104~117 | line 104~117 (`HF_TOKEN` 체크 + 실패 시 exit 1) | ✅ |
| repo-id 형식 grep 패턴 | line 90~94 | line 90~94 (`grep -qE "^[^/]+/[^/]+$"`) | ✅ |
| CLI 인터페이스 (`--dataset`, `--repo-id`, `--private`) | §5 transfer_to_hub() 인자 | 스크립트 line 50~53 | ✅ |

### sync_dataset_collector_to_dgx.sh

| 검증 항목 | 문서 기술 | 실제 파일 | 일치 |
|---|---|---|---|
| 실행 위치 (devPC) | "line 6: devPC" | 실제 line 4: "실행 위치: devPC (어디서든)" | ⚠️ Recommended #2 (내용 정확, 라인 번호 부정확) |
| SSH alias 확인 | line 67~77 | line 67~77 (`grep -q "^Host datacollector"`) | ✅ |
| DataCollector→devPC rsync | line 117~123 | line 118~123 | ✅ 허용 범위 |
| devPC→DGX rsync | line 126~136 | line 129~136 | ✅ 허용 범위 |

---

## §3 flow 5 옵션 후보 검증

- 후보 수: 5개 — spec 제약 `≤5개` 충족 ✅
- 각 후보에 `--dataset.single_task` 값 명시 ✅
- 권장 후보 (후보 1 단순 pick-place) 근거 — `svla_so100_pickplace` 사전학습 태스크와 동일 도메인 명시 ✅
- `tokenizer_max_length=48` 제약 내 영문 task instruction 확인 ✅

---

## §5 flow 7 rsync 분기 정확성 검증

- `sync_dataset_collector_to_dgx.sh` 는 devPC 전용 — 문서에 "datacollector 에서 직접 호출 X, devPC 명령 안내" 로 정확히 처리 ✅
- `guide_rsync_to_dgx()` 함수가 직접 실행 없이 안내 메시지 출력으로 대체 ✅
- HF Hub 분기: `push_dataset_hub.sh` datacollector 에서 직접 호출 (실행 위치: DataCollector 머신 또는 devPC ssh 경유 — `push_dataset_hub.sh` line 4 확인) ✅

---

## awaits_user-A 발송 명세 검증

- `01_implementation.md` 에 발송 내용 사용자 가독 형식 (한국어 + 영문 인자 병기) 작성 ✅
- `15_datacollector_cli_flow.md` §3 에 동일 내용 재수록 ✅
- 각 후보: 이름·설명·task instruction·`lerobot-record` 인자·권장 에피소드 수 명시 ✅
- D2 영향 명시 (`data_kind.py` 분기 + `record.py` draccus 인자 동적 생성) ✅
- 복수 선택·다른 후보 제안 가능 안내 ✅

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | orin/lerobot/ 및 pyproject.toml 미변경 — 해당 없음 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | 문서 §5 내 Python 코드 블록은 구현 설계 명세 (bash 명령 예시 추가와 다름) — 위반 없음 |
| Category C | ✅ | 새 디렉터리 생성 없음 (`docs/storage/` 기존 디렉터리에 파일 추가) |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 없음 (study todo). code-tester 통과로 종료.

단, awaits_user-A 답 수신 전 D2 dispatch 보류 (orchestrator 책임).
