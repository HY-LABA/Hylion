# TODO-L2 — Code Test

> 작성: 2026-05-02 14:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 2건.

---

## 단위 테스트 결과

```
해당 없음 — TODO-L2 는 git mv 이관 + README 신규 작성 작업. 실행 가능 코드 변경 없음.
pytest 대상 없음.
```

## Lint·Type 결과

```
해당 없음 — Python 파일 수정 없음. README.md 신규 작성 (Markdown).
ruff check / mypy 대상 없음.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `docs/storage/legacy/02_datacollector_separate_node/` 신규 디렉터리 생성 | ✅ | `ls` 확인: 8건 (datacollector/ + docs_storage_* 3건 + scripts_* 3건 + README.md) |
| 2. `datacollector/` 전체 git mv (git R 인식) | ✅ | `git status`: datacollector/ 하위 17개 파일 모두 `R` rename 인식. `datacollector/` 디렉터리 smolVLA 루트에서 완전 제거 확인 |
| 3. `docs/storage/07/10/15_datacollector_*.md` → prefix 변환 git mv | ✅ | `git status`: 3건 모두 `R` 인식. 원래 위치에 파일 없음 확인 |
| 4. `scripts/sync_dataset_*`, `sync_ckpt_*`, `deploy_datacollector.sh` → prefix 변환 git mv | ✅ | `git status`: 3건 모두 `R` 인식. 원래 위치에 파일 없음 확인 |
| 5. `02_datacollector_separate_node/README.md` 신규 작성 (이동 사유·일자·후속·DataCollector 머신 운영 종료) | ✅ | 이관 일자 2026-05-02, 06 결정 배경 2개 동력, 자산 목록 전체, 머신 운영 종료 안내, 후속 X 그룹 연결 모두 포함 |
| 6. 하드코딩 잔재 grep + 인계 항목 보고 | ✅ | §2 그리드에 11개 파일 목록화. 처리 주체 (M3/X2) 명시. history/context 제외 사유도 기재 |
| 7. `datacollector/` 완전 제거 확인 | ✅ | `ls smolVLA/ | grep datacollector` — 미출력 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/work_flow/context/todos/L2/01_implementation.md` §2 grep 결과 표 — `dgx/interactive_cli/flows/training.py` 행 | 보고서는 `line 15, 70, 72` (3건) 로 기재했으나 실제 grep 결과는 7건 (L15, L54, L70, L72, L92, L494, L497). line 번호 불완전 기재 — X2 에서 수정 시 참조 기준이 어긋날 수 있음. 인계 문서 정확도 개선 권장 |
| 2 | `docs/work_flow/context/todos/L2/01_implementation.md` §2 grep 결과 표 — `orin/interactive_cli/README.md`, `dgx/interactive_cli/README.md` 행 | 보고서는 `line 50` 1건만 명시했으나 실제로는 L7·L8·L35·L37·L39·L50 총 6건 (orin·dgx 동일). `deploy_datacollector` 외 `datacollector` 노드 명시 행도 포함됨 — M3·X2 처리 시 전체 행 정정 필요. 인계 문서에 line 범위 보강 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/`, `.claude/skills/` 미변경. CLAUDE.md 자체 수정은 spec E 결정에 따른 Phase 1 메인 Claude 직접 수정 (사용자 승인 완료) — task-executor 위반 아님 |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `dgx/lerobot/` 미변경. `orin/pyproject.toml`, `dgx/pyproject.toml` 미변경 (이동된 `datacollector/pyproject.toml` 은 legacy 행 — 활성 의존성 아님). `orin/scripts/setup_env.sh`, `dgx/scripts/setup_env.sh` 미변경. `scripts/deploy_*.sh` 는 legacy 이관 대상 (삭제가 아닌 rename) |
| Coupled File Rules | ✅ | `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요. `orin/pyproject.toml` 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요 |
| D (절대 금지 명령) | ✅ | `rm -rf` 미사용. `git mv` 로만 처리 |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 명령 예시 추가 없음 (README.md는 이관 기록 문서, 명령 예시 아님) |

---

## 검증 명령 수행 기록

```
1. git status --short | grep "^R " | grep -c "datacollector"
   → 23 (datacollector 관련 rename 23건 인식)

2. git status --short | grep "^R " | grep -E "07_datacollector|10_datacollector|15_datacollector|sync_dataset|sync_ckpt_dgx|deploy_datacollector"
   → 6건 모두 R 인식 확인

3. ls smolVLA/ | grep "^datacollector$"
   → 미출력 (완전 제거 확인)

4. ls docs/storage/ | grep -E "07_|10_|15_datacollector"
   → 미출력 (원래 위치 파일 없음)

5. ls scripts/ | grep -E "sync_dataset|sync_ckpt_dgx|deploy_datacollector"
   → 미출력 (원래 위치 파일 없음)

6. ls docs/storage/legacy/02_datacollector_separate_node/
   → datacollector/, docs_storage_07_*, docs_storage_10_*, docs_storage_15_*, README.md,
      scripts_deploy_datacollector.sh, scripts_sync_ckpt_dgx_to_datacollector.sh,
      scripts_sync_dataset_collector_to_dgx.sh (8건 전체 확인)

7. grep 인계 항목 재확인:
   - training.py: sync_ckpt_dgx_to_datacollector 7건 확인 (L15, L54, L70, L72, L92, L494, L497)
   - orin/README.md: deploy_datacollector L50 + 추가 datacollector 참조 L7~L39
   - dgx/README.md: deploy_datacollector L50 + 추가 datacollector 참조 L7~L39

8. Category A/B 영역 변경 없음 확인:
   - .claude/ 변경 없음
   - lerobot/ 변경 없음
   - orin/dgx pyproject.toml, setup_env.sh 변경 없음
   - M 상태 파일: CLAUDE.md (Phase 1 E 결정), log.md, plan.md (오케스트레이터 관리)
```

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

git mv 7건 모두 R 인식, `datacollector/` 디렉터리 완전 제거, 이름 prefix 일관성 (docs_storage_* / scripts_*), README.md DOD 요건 전체 충족. Recommended 2건은 인계 문서 라인 번호 정확도 문제로 후속 todo (X2·M3) 수행에 지장 없음.
