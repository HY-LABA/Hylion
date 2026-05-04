# TODO-P5 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

---

## 배포 대상

- 없음 (AUTO_LOCAL 환경 레벨 — devPC 로컬 grep + syntax 검증)
- SSH 배포 불요. 변경 파일이 orin/, dgx/ 코드 변경이 아닌 docstring·주석·텍스트 정리이므로 prod 배포 없이 로컬 검증으로 DOD 전 항목 충족 가능

---

## 배포 결과

- 해당 없음 (AUTO_LOCAL)

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| bash -n syntax | `bash -n orin/interactive_cli/main.sh` | PASS |
| py_compile (orin entry) | `python3 -m py_compile orin/interactive_cli/flows/entry.py` | PASS |
| py_compile (dgx entry) | `python3 -m py_compile dgx/interactive_cli/flows/entry.py` | PASS |
| py_compile (training) | `python3 -m py_compile dgx/interactive_cli/flows/training.py` | PASS |
| json.tool | `python3 -m json.tool dgx/config/dataset_repos.json` | PASS (valid JSON) |
| 잔재 grep (orin/dgx/scripts) | `grep -rIn -E "datacollector\|smallgaint" ... orin/ dgx/ scripts/` | 활성 잔재 0건 (하기 분류 참조) |
| 잔재 grep (docs/lerobot_study) | 동일 패턴, docs/lerobot_study/ 대상 | 0건 |
| 잔재 grep (루트 파일) | pyproject.toml, Makefile 등 | 0건 |

### grep 잔재 분류 상세

orin/ + dgx/ + scripts/ grep 결과에서 남아있는 `datacollector` 매치 전수 분류:

| 파일 | 잔재 패턴 | 분류 |
|---|---|---|
| orin/interactive_cli/flows/entry.py L21~23 | `VALID_NODES 변경 이력 기록` 주석 블록 | 의도된 이력 주석 |
| orin/interactive_cli/flows/entry.py L48, L121 | 갱신 이력 주석 (`갱신 (2026-05-02, TODO-X2)`) | 의도된 이력 주석 |
| orin/interactive_cli/README.md L7~8, L11, L37~40, L53, L58 | 정정 주석·HTML 주석 안 역사적 설정 보존·legacy 이관 완료 주석 | 의도된 이력 주석 |
| orin/interactive_cli/main.sh L16 | `(datacollector 노드는 06_dgx_absorbs_datacollector 결정으로 운영 종료)` | 의도된 운영 종료 주석 (P5 정리 산출물) |
| dgx/interactive_cli/flows/entry.py L17~18, L37, L110 | 갱신 이력 주석 | 의도된 이력 주석 |
| dgx/interactive_cli/README.md L7~8, L11, L42~45, L58, L63 | 정정 주석·HTML 주석·legacy 이관 완료 주석 | 의도된 이력 주석 |
| dgx/README.md L6, L187~189 | 갱신 이력 노트 + HTML 주석 이력 (R#1 산출물) | 의도된 이력 주석 |
| dgx/scripts/push_dataset_hub.sh L3~8 | 이식 이력 주석 (원본 경로 비교) | 의도된 이식 이력 |
| dgx/scripts/run_teleoperate.sh L5~6, L9, L21 | 이식 이력 주석 (원본 경로 비교) | 의도된 이식 이력 |
| dgx/interactive_cli/flows/record.py L56~61, L178, L204, L312, L316 | 이식 이력·원본 경로 비교 주석 | 의도된 이식 이력 |
| dgx/interactive_cli/flows/data_kind.py L14, L18, L91 | 이식 이력·원본 참조 주석 | 의도된 이식 이력 |
| dgx/interactive_cli/flows/env_check.py L73 | 이식 이력 주석 (미러 패턴) | 의도된 이식 이력 |
| dgx/interactive_cli/flows/transfer.py L3, L8, L12 | 이식 이력·결정 근거 주석 | 의도된 이식 이력 |
| dgx/interactive_cli/flows/mode.py L3, L17 | 이식 이력·패턴 참조 주석 | 의도된 이식 이력 |
| dgx/interactive_cli/flows/training.py L17, L62, L64, L504 | 인용 제거 이력 주석 (R#2 포함 cycle 1 분류 확인됨) | 의도된 이력 주석 |
| dgx/scripts/setup_train_env.sh L69, L84 | 결정 이력·버전 범위 인용 출처 주석 | 의도된 이력 주석 |
| dgx/config/dataset_repos.json L2 | 운영 종료 경과 주석 (P5 정리 산출물) | 의도된 운영 종료 주석 |
| dgx/config/README.md L3 | 운영 종료 경과 주석 (P5 정리 산출물) | 의도된 운영 종료 주석 |

**활성 잔재: 0건. 모든 매치가 의도된 이력/정정/이식/운영종료 주석 패턴.**

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. orin/ 활성 잔재 0건 | grep (AUTO_LOCAL) | ✅ 0건 (main.sh L16, entry.py 4건 처리 완료. 나머지 이력 주석) |
| 2. dgx/ 활성 잔재 0건 | grep (AUTO_LOCAL) | ✅ 0건 (entry.py 3건 + dataset_repos.json + config/README.md + README.md R#1 + training.py R#2 처리 완료) |
| 3. scripts/ 잔재 0건 | grep (AUTO_LOCAL) | ✅ 0건 (P1 이 dev-connect.sh 처리. 나머지 이식 이력 주석) |
| 4. docs/lerobot_study/ 잔재 0건 | grep (AUTO_LOCAL) | ✅ 0건 |
| 5. pyproject.toml / Makefile 잔재 0건 | grep (AUTO_LOCAL) | ✅ 0건 |
| 6. bash -n / py_compile / json.tool PASS | syntax check (AUTO_LOCAL) | ✅ 전 파일 통과 |
| 7. P1·P2·P3·P4 영역과 겹침 없음 | 파일 목록 대조 | ✅ P5 변경 8건이 P1(dev-connect.sh)·P2(.gitignore)·P3(arm_2week_plan.md)·P4(specs/README.md) 와 완전 분리 |

---

## R#1 처리 적정성 — `dgx/README.md`

처리 방식 확인: (b) 의미 재작성 채택 (단순 삭제 X).

- L5 헤더 갱신 노트 추가: 기존 "DataCollector 인터페이스 안내 추가" → "데이터 수집 인터페이스 안내 추가" (중립 표현) + P5 갱신 이력 추가
- L16 entrypoint 설명: "나머지는 DataCollector / Orin 의 책임" → "데이터 수집·텔레오퍼레이션은 DGX 가 직접 담당, 추론은 Orin 의 책임" (현 3-노드 구조 반영)
- L44 directory tree: "DataCollector 로부터 수신할 HF 데이터셋" → "DGX 학습에 사용할 HF 데이터셋"
- L184~202 섹션 완전 재작성: "DataCollector ↔ DGX 인터페이스" → "DGX 단일 노드 데이터 수집·학습 인터페이스" + HTML 이력 주석 + DGX→DGX→Orin 흐름도

판정: 의미 보존 재작성 확인. 06_dgx_absorbs_datacollector 결정 사실이 본문과 주석에 자연스럽게 반영됨.

---

## R#2 처리 적정성 — `dgx/interactive_cli/flows/training.py` L284

Before: `"로컬 데이터셋이 없습니다. 먼저 DataCollector 에서 rsync 를 실행하세요."`

After: `"로컬 데이터셋이 없습니다. DGX 에서 lerobot-record 로 데이터 수집 후 학습을 진행하세요."`

판정:
- 현 워크플로우 (DGX 자체 수집·학습) 반영: "DGX 에서 lerobot-record 로 수집" — 정확
- 한국어 자연스러움: "데이터 수집 후 학습을 진행하세요" — 자연스러운 표현
- 사용자 노출 print() 문으로 기능 오동작 없이 안내 정확성 개선 확인

---

## 사용자 실물 검증 필요 사항

없음. 본 todo 는 docstring·주석·텍스트 정리 작업이며 모든 DOD 항목이 AUTO_LOCAL 검증으로 충족됨.

---

## CLAUDE.md 준수

| Category | 체크 | 메모 |
|---|---|---|
| prod-test-runner 자율성 | ✅ 자율 | AUTO_LOCAL — SSH 배포 없음. 로컬 bash -n, py_compile, json.tool, grep 만 실행 |
| Category B 영역 변경 배포 | 해당 없음 | 변경 파일 8건 모두 Category B 외 (lerobot/, pyproject.toml, setup_env.sh, deploy_*.sh 미해당) |
| Category A 영역 | ✅ | docs/reference/ 미변경. .claude/ 미변경 |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경, orin/pyproject.toml 미변경 → diff 갱신 불요 |
| 동의 필요 영역 없음 | ✅ | 큰 다운로드 X, 긴 실행 X, 가상환경 재생성 X |
