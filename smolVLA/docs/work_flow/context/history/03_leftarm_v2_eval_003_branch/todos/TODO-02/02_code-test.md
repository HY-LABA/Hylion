# TODO-02 — Code Test

> 작성: 2026-05-19 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건, Recommended 1건.

---

## 단위 테스트 결과

```
해당 없음 — TODO-02 산출물은 문서 파일 (003_eval_2026-05-19.md) 신규 작성.
코드 파일 변경 없음 → pytest 실행 대상 없음.
Category B (run_inference_leftarm_v2.sh) 수정 없음 → wrapper 단위 테스트 불요.
```

## Lint·Type 결과

```
해당 없음 — 신규 산출물이 .md 파일 1개 + task-executor 보고서 1개.
Python 코드 변경 없음 → ruff / mypy 실행 대상 없음.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) Orin 003 ckpt 다운로드 + smoke | 사용자 위임 | SSH 차단 — 환경 차단(시연장 이동)으로 devPC 도달 불가. verification_queue PHYS_REQUIRED 등록 합리적. task-executor 미완 아님. |
| (b) `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 신설 — 양식 mirror | ✅ | camera_empty_eval_2026-05-18.md 양식 mirror 확인. 메타·평가기준·Trial 골격·결과집계·종합정성·다음단계 모두 존재. |
| (c) Orin 측 cal·rotation·camera config·inference wrapper 정합 확인 | ✅ (일부 사용자 위임) | HF Hub 원격 검증 (empty_cameras=1, n_action_steps=50, adapter 44MB) 완료. wrapper 코드 분석으로 환경 변수 override 정합 확인. Orin 실측 config (ports/cameras null 여부) 는 SSH 차단으로 미확인 — trial 시작 전 사용자 체크리스트 시트에 명시됨. |
| Category B (run_inference_leftarm_v2.sh) 수정 X | ✅ | 코드 변경 없음. 환경 변수 override 만 사용 확인. |

---

## A. 003_eval 양식 mirror 검증

### 메타 섹션

정본(camera_empty_eval_2026-05-18.md)의 메타 항목 9개 모두 대응:
- 평가 대상 ckpt, ckpt 형태, 학습 메타 요약, 평가일, 평가자, 평가 환경, 사이클 비고, 선행 사이클 보고서 — 모두 정합.
- 003_eval 에 `spec`/`plan` 링크 항목 추가 — 정본에 없는 개선 항목. 정합성 문제 없음.
- `[TODO-01 완료 후 인용]` 마커: 학습 메타 요약 항목 내 `final loss` / `학습 시간` 2곳에 명시. 위치 적절.

### 평가 기준 섹션

| 항목 | 정본 존재 | 003_eval 존재 | 정합 |
|---|---|---|---|
| 평가 지표 (success rate + 2차·3차 메트릭) | ✅ | ✅ | 일치 |
| 시나리오 구성 표 (4×5=20) | ✅ | ✅ | 일치 |
| Task instruction 정본 (task1·task2) | ✅ | ✅ | 일치 |
| 성공 정의 표 | ✅ | ✅ | 일치 |
| 실패 원인 분류 코드 표 | ✅ | ✅ | 일치 |
| 재시도 처리 정책 | ✅ (간략) | ✅ (확장 — 무효 분모 제외 명시) | 개선 |
| trial 시작 전 USB 체크리스트 | ❌ (없음) | ✅ (신설) | 003 신규 추가 — 합리적 |

### Trial 기록 섹션

4그룹 × 5trial = 20행 빈 골격 완전 존재 확인:
- task1 × front: trial 1~5
- task1 × back: trial 6~10
- task2 × front: trial 11~15
- task2 × back: trial 16~20
- 각 행: trial #, task, orientation, 성공, 실패 원인 분류, 자유 메모 — 정본과 동일.

### 결과 집계 섹션

- 그룹별 빈 골격 (`— / —`, `—`) 존재 확인.
- `(현재: 빈 골격)` 명시 — TODO-04 채움 명시.
- M1.5 · 002 · 003 비교 표 골격 존재 (M1.5·002 실적값 기인용 포함).

### 종합 정성 메모 섹션

정본의 4개 항목 모두 대응 + 003 신규 항목 추가:
- 두 task 구분 응답성 ✅
- 6:4 편향 영향 관찰 ✅
- 동작 품질 정성 관찰 ✅
- (M2→) M4 본 학습 진입 가치 판단 ✅
- **신규**: 5변수 종합 효과 판단 (003 사이클 특유) ✅

결론: **mirror 정합. 구조적 차이 없음. 003 특유 항목은 모두 합리적 신설.**

---

## B. 학습 메타 인용 정합성

- `[TODO-01 완료 후 인용]` 마커 위치: 메타 섹션 `학습 메타 요약` 행 내 — 적절.
- TODO-04 자동 인용 가능성: 마커가 `final loss` / `학습 시간` 2개 필드에 명시됨. TODO-04 단계에서 `learning_log.md §003` 의 해당 수치를 직접 인용 가능한 형태. **가능.**

---

## C. HF 원격 검증 정합

task-executor 보고서 기준:

| 항목 | 보고 값 | 정합 여부 |
|---|---|---|
| HF Hub repo 파일 구조 | siblings 8개 + README + .gitattributes = 10개 존재 | ✅ |
| `config.json.empty_cameras` | 1 | ✅ (003 분기 정합) |
| `config.json.n_action_steps` | 50 | ✅ |
| `adapter_model.safetensors` 크기 | 44MB (46,201,840 bytes) | ✅ |

**n_action_steps=50 spec/plan 정합성**: plan 가정 §max-steps 에 `run_inference_leftarm_v2.sh live max-steps=1000` 정합 확인됨. n_action_steps=50 은 wrapper line 189 `--n-action-steps 50` (dry-run) / line 256 `--n-action-steps 50` (live) 에서 일치. M1.5/002 와 동일값 — 추론 패턴 일관성 확보. **spec/plan 정합 확인.**

---

## D. wrapper 코드 분석 — Category B 미발동 확정

`run_inference_leftarm_v2.sh` 분석 결과:

| 확인 항목 | 결과 |
|---|---|
| 코드 변경 여부 | **없음** — task-executor 가 Read + Bash 환경 변수 override 만 수행 |
| `dry-run` subcommand 지원 | ✅ (cmd_dry_run — `--max-steps 1` smoke) |
| `live` subcommand 지원 | ✅ (cmd_live task1/task2) |
| `download` subcommand 지원 | ✅ (cmd_download — hf/huggingface-cli fallback) |
| `CKPT_REPO_ID` 환경 변수 override | ✅ (line 32: `CKPT_REPO_ID="${CKPT_REPO_ID:-BaboGaeguri/leftarm_v2_A2_pc_2026-05-17}"`) |
| `CKPT_LOCAL_DIR` 환경 변수 override | ✅ (line 33) |
| live `--max-steps 1000` 하드코딩 | ✅ (line 257 — BACKLOG #13 완료 일치) |
| Category B 미발동 | **확정** |

---

## E. SSH 차단 처리 합리성

**환경 차단 vs task 미완 판단**: 사용자가 시연장으로 이동함에 따라 Orin(172.16.134.117) 이 devPC 에서 도달 불가 상태. 이는 사용자의 *의도된 이동*에 의한 네트워크 단절 — task-executor 의 책임이 없는 *환경 차단*. **합리적 분리 확정.**

**사용자 위임 명령 시퀀스** (task-executor 보고서 §사용자 PHYS_REQUIRED 준비 상태):

| Step | 명령 | wrapper subcommand 일치 |
|---|---|---|
| A. 환경 확인 | `source orin/.hylion_arm/bin/activate` + config 확인 | 해당 없음 (사전 확인) |
| B. 003 ckpt 다운로드 | `export CKPT_REPO_ID=...` + `bash ... download` | `cmd_download` ✅ |
| C. dry-run smoke | `bash ... dry-run task1` | `cmd_dry_run task1` ✅ |
| D. live trial | `bash ... live task1` / `bash ... live task2` | `cmd_live task1/task2` ✅ |

**wrapper 실제 subcommand 와 일치 확인.** 명령 시퀀스 완전.

또한 003_eval 시트 내 `trial 시작 전 체크리스트` 섹션에 환경 변수 override 예시 명령이 직접 포함됨 — 사용자가 시트 열람만으로 실행 가능.

---

## F. Hard Constraints 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ 통과 | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ 통과 | `run_inference_leftarm_v2.sh` 코드 변경 없음. `orin/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경. |
| Coupled File Rules | ✅ 해당 없음 | Category B 영역 미변경 → coupled file 갱신 불필요 |
| C (사용자 동의 필수) | ✅ 통과 | `orin/docs/leftarm_v2/` 기존 디렉터리 내 신규 파일 추가 — Category C 미해당 |
| D (절대 금지 명령) | ✅ 통과 | rm -rf, sudo 등 미사용 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ 해당 없음 | `docs/storage/` 미변경 |

---

## G. spec 본문 가정 충족 검증

| 가정 | 확인 방법 | 결과 |
|---|---|---|
| 가정 1 (HF Hub push 완료) | task-executor curl/HF API 원격 검증 | ✅ — repo 존재 + 파일 구조 완전 확인 |
| 가정 2 (empty_cameras 패치 자동 적용) | HF `config.json.empty_cameras=1` 확인 (원격). Orin smoke 는 사용자 위임. | ✅ (원격 부분) / 사용자 위임 (Orin 실행) |
| 가정 5 (max-steps=1000) | wrapper 코드 line 257 직접 확인 | ✅ — `--max-steps 1000` 하드코딩 확인 |
| 가정 7 (신규 파일 추가 X) | wrapper 코드 분석 | ✅ — 기존 파일 그대로, 환경 변수 override 만 |
| 가정 8 (orin/docs/leftarm_v2/ 기존) | 기존 디렉터리 내 신규 파일 — Category C 미해당 | ✅ |

모두 정합 (원격 검증 가능한 범위 내).

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `003_eval_2026-05-19.md` Trial 기록 섹션 task1×front 이후 그룹 헤더 | task1×front 헤더에만 `CKPT_REPO_ID=...` 전체 명시되고 이후 그룹엔 없음. 사용자 혼란 없으나 trial 시작 전 체크리스트에 전체 명령이 이미 포함됨 — 영향 없음. 다음 사이클 시트 작성 시 일관화 권장. |

---

## CLAUDE.md 준수 체크 요약

| Category | 결과 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | Category B 영역 전체 미변경 — 미발동 확정 |
| Coupled File Rules | ✅ | 해당 없음 |
| C·D | ✅ | 미해당·미사용 |

---

## prod-test-runner 검증 가능 영역

| 영역 | 환경 레벨 | 내용 |
|---|---|---|
| `003_eval_2026-05-19.md` 형식·구조 | `AUTO_LOCAL` | 이미 code-tester 가 본 보고서에서 검증 완료. prod-test-runner 추가 구조 확인 가능 (파일 존재, 20행 완전성 grep 등). |
| HF Hub 원격 검증 | `AUTO_LOCAL` | task-executor 보고 수치 재현 검증 가능 (curl HF API). |
| Orin 003 ckpt 다운로드·dry-run·live | `PHYS_REQUIRED` | SSH 차단. 사용자가 시연장 Orin 에서 직접 실행 — verification_queue 등록 필요. |

**prod-test-runner 권고**: devPC AUTO_LOCAL 검증 후 Orin PHYS_REQUIRED 항목은 `verification_queue.md` 에 `NEEDS_USER_VERIFICATION` 으로 등록.

---

## 배포 권장

**READY_TO_SHIP** — prod-test-runner 진입 권장.

- devPC 산출물 (`003_eval_2026-05-19.md`) 완전히 완료됨.
- HF Hub 원격 검증 (empty_cameras=1, n_action_steps=50, adapter 44MB) 정합.
- wrapper 코드 분석으로 Category B 미발동 확정.
- SSH 차단은 환경 차단 (사용자 시연장 이동 의도된 상태) — task-executor 미완 아님.
- 사용자 위임 명령 시퀀스 완전 (Step A~D, wrapper subcommand 전체 일치).
- Orin PHYS_REQUIRED 검증은 verification_queue 에 합산 등록 후 사용자 현장 수행.
