# TODO-X1 — dgx/ 구조·기능 책임 매트릭스

> 작성: 2026-05-01 | task-executor | cycle: 1

## 사전 점검 결과

### 현재 dgx/ 트리

```
dgx/
├── README.md
├── runs/README.md
└── scripts/
    ├── preflight_check.sh
    ├── save_dummy_checkpoint.sh
    ├── setup_train_env.sh
    └── smoke_test.sh
```

- `dgx/pyproject.toml` 미존재 — 학습은 `docs/reference/lerobot/` editable 설치로 upstream entrypoint 그대로 사용
- `dgx/lerobot/` curated 디렉터리 미존재 — orin/ 과 달리 코드 트리밍 불필요
- `dgx/outputs/` + `dgx/.arm_finetune/` 는 런타임 생성 (gitignore)

### 02 산출물 위치 확인

4개 스크립트 모두 `dgx/scripts/` 에 존재 확인:
- `setup_train_env.sh` — venv + PyTorch + lerobot editable 설치
- `preflight_check.sh` — OOM/Walking RL 보호 게이트
- `smoke_test.sh` — 1-step 학습 검증
- `save_dummy_checkpoint.sh` — dummy ckpt 생성 (DGX→Orin 전송 검증)

`04_dgx_lerobot_diff.md` — 이미 존재 (`docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md`). 02 마일스톤 산출물로 smoke_test.sh 보정 이력 포함.

### 06_dgx_venv_setting.md 핵심 사실

- Python 3.12.3 (DGX 시스템)
- torch 2.10.0+cu130 (Walking RL 검증 완료)
- lerobot editable (docs/reference/lerobot/ submodule, v0.5.1-52-g05a52238, `[smolvla,training]`)
- HF_HOME: `~/smolvla/.hf_cache` (Walking RL 격리)
- GB10 CUDA capability 12.1 UserWarning — 기능 정상
- smoke test 실측: 5.97 초/step, RAM peak 48 GiB (batch=8, Walking RL 동시 점유)
- Walking RL 동시 점유 시 OOM 없이 동작 확인. batch=64 + S3 시 OOM 마진 재검토 권장

### run_teleoperate.sh 임시 보관 위치 확인

`docs/storage/others/run_teleoperate.sh.archive` — TODO-O2 에서 임시 보관된 상태. DataCollector 디렉터리 미존재로 TODO-D2 까지 대기 중.

### 04_dgx_lerobot_diff.md 존재 여부

이미 존재 — TODO-X2 에서 dgx/ 코드 변경 (scripts/ 내 신규 코드 작성) 이 있을 경우 해당 시점에 추가 이력 기입 필요. 본 TODO-X1 은 study 이므로 변경 없음.

---

## 산출물

- `docs/storage/08_dgx_structure.md` — 신규 작성 (07_orin_structure.md 패턴 미러)

### 절별 요약

| 절 | 제목 | 핵심 내용 |
|---|---|---|
| §0 | 본 문서의 위치 | DGX 학습 전용 책임 명확화. upstream 무수정 원칙 |
| §1 | 디렉터리 트리 | 현재 (5개 파일) + 새 구조 (tests/, config/ 신규 추가) |
| §2 | 핵심 컴포넌트 책임 표 | 9개 컴포넌트 (기존 7 + 신규 2) × 책임·04 변경 여부 |
| §3 | 마일스톤별 책임 매트릭스 | 9 마일스톤 (00~08) × 8 컴포넌트 |
| §4 | 외부 의존성 | devPC sync hub / HF Hub / DataCollector 인터페이스 / 시스템 의존성 / Walking RL 보호 정책 |
| §5 | 마이그레이션 계획 | 5개 카테고리 (유지 7건 / 이관 1건 / 신규 3건 / 삭제 0건 / entrypoint 정리) |
| §6 | 향후 TODO 트리거 | X2 / X3 / T1 / T2 / D2 연결점 |

---

## 핵심 결정

### run_teleoperate.sh 최종 위치 권고: (a) DataCollector

- DGX 는 SO-ARM 직접 연결 없음 → run_teleoperate.sh 실행 불가
- teleop = 시연장 인근 데이터 수집 일부 → DataCollector 의 책임
- 최종 위치: `datacollector/scripts/run_teleoperate.sh` (TODO-D1 디렉터리 확정 후 TODO-D2 에서 이동)
- 현재: `docs/storage/others/run_teleoperate.sh.archive` 임시 보관 유지

### DataCollector ↔ DGX 인터페이스

- HF Hub vs rsync 둘 다 옵션
- **TODO-T1 awaits_user 답에 따라 §5-3 config/dataset_repos.json 스키마 일부 갱신 필요**
- HF Hub 방식 (권장): DataCollector 에서 `lerobot-record --push-to-hub` → DGX 에서 `lerobot-train --dataset.repo_id=<HF_USER>/...`
- rsync 직접: `scripts/sync_dataset_collector_to_dgx.sh` (TODO-T1 결정 시 작성)
- 인터페이스 포맷: LeRobotDataset (lerobot 표준) — DGX 와 DataCollector 모두 동일 lerobot upstream 사용이므로 포맷 불일치 없음

### TODO-X2 마이그레이션 5개 카테고리

| 카테고리 | 내용 |
|---|---|
| 유지 | scripts/ 4개 + runs/README.md + README.md + .arm_finetune/ (7건) |
| 이관 (out) | run_teleoperate.sh archive → DataCollector (TODO-D2 시점) |
| 신규 (in) | dgx/tests/ + README.md / dgx/config/ + README.md + dataset_repos.json (3건) |
| 삭제 | 없음 |
| entrypoint 정리 | pyproject.toml 미존재이므로 해당 없음. README.md 에 DataCollector 책임 entrypoint 주의사항 명시 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (read-only 레퍼런스 활용만)
- Coupled File Rule: `dgx/lerobot/` 변경 없음 → `04_dgx_lerobot_diff.md` 갱신 불필요 (본 TODO). 기존 파일 존재 확인 완료
- 레퍼런스 활용: `07_orin_structure.md` 의 §0~§6 절 구성 패턴 미러. `06_dgx_venv_setting.md` 실측 사실 §1 / §4 에 반영
- lerobot-reference-usage 스킬: study 타입 (신규 코드 X) — SKILL_GAP 해당 없음
- lerobot-upstream-check 스킬: `dgx/pyproject.toml` 미존재이므로 coupled file 규칙 적용 대상 없음. Category B 주의사항: TODO-X2 에서 dgx/scripts/ 에 신규 스크립트 추가 시 `04_dgx_lerobot_diff.md` 이력 추가 권장

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/08_dgx_structure.md` | 신규 | DGX 구조·책임 매트릭스 + 마이그레이션 계획 (07_orin_structure.md 패턴 미러) |
| `docs/work_flow/context/todos/X1/01_implementation.md` | 신규 | 본 파일 (TODO-X1 구현 보고서) |
| `docs/work_flow/context/history/04_infra_setup/<timestamp>_task_dgx_structure.md` | 신규 | 작업 history 기록 (별도 작성 예정) |

---

## 잔여 리스크 / SKILL_GAP / Anomaly

- SKILL_GAP 없음 (study 타입, 신규 코드 없음)
- **인터페이스 미결**: DataCollector ↔ DGX 데이터 전송 방식 (HF Hub vs rsync) — TODO-T1 `awaits_user` 답에 달림. `dgx/config/dataset_repos.json` 스키마는 T1 결정 후 갱신 필요
- **Category B 주의**: TODO-X2 에서 `dgx/scripts/` 에 신규 스크립트 작성 시 코드 수정이 발생 → `04_dgx_lerobot_diff.md` 에 이력 추가 권장 (CLAUDE.md coupled file 규칙)
- **DataCollector 미확정**: run_teleoperate.sh 의 최종 위치 이동은 TODO-D1 (노드 정체 결정) → TODO-D2 (셋업 스크립트 + datacollector/ 신규) 순서를 기다림
- **batch_size 증가 시 preflight 임계치 재검토**: 06_dgx_venv_setting.md §8 — batch=64 시 RAM 추가 점유 가능, s1 (35 GiB) 임계치 충분성 미확인

---

## 검증 필요 (다음 단계: code-tester)

code-tester 는 study 타입이라 코드 검증 불필요. 산출물 일관성 + 패턴 미러 검증:

- 07_orin_structure.md 와 동일 절 구조 (§0~§6) 준수 여부
- §3 마일스톤 매트릭스 9개 마일스톤 (00~08) 모두 포함 여부
- §4-3 DataCollector ↔ DGX 인터페이스: TODO-T1 awaits_user 미결 상태 명시 여부
- §5 run_teleoperate.sh 결정 (후보 a DataCollector 채택) 근거 명시 여부
- 04_dgx_lerobot_diff.md 존재 확인 + TODO-X2 갱신 시점 명시 여부
- CLAUDE.md Category B 영역 (dgx/lerobot/, dgx/pyproject.toml) 변경 없음 — 본 TODO 는 study 이므로 해당 없음. TODO-X2 에서 발생 가능성 명시 여부
