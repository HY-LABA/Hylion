# TODO-W2 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`docs/storage/lerobot_upstream_check/99_lerobot_upstream_Tracking.md` 에 디렉터리 파일 색인 섹션 신설 — `04_dgx_lerobot_diff.md`·`05_datacollector_lerobot_diff.md` 포함 전체 파일 등록 또는 미등록 사유 명시.

---

## Step 1 — 디렉터리 현 상태

```
docs/storage/lerobot_upstream_check/
├── 01_compatibility_check.md
├── 02_orin_pyproject_diff.md
├── 03_orin_lerobot_diff.md
├── 04_dgx_lerobot_diff.md
├── 05_datacollector_lerobot_diff.md
├── check_update_diff.sh
└── 99_lerobot_upstream_Tracking.md
```

`README.md` 또는 `00_*` 색인 파일 미존재 확인. `99_lerobot_upstream_Tracking.md` 가 색인 역할 대행 (plan.md 사전 정정 사항 확인).

---

## Step 2 — 기존 색인 파일 등록 상태 확인

`99_lerobot_upstream_Tracking.md` 는 "Upstream Tracking Log" 테이블 (commit 이력) 만 보유. 디렉터리 내 파일 색인 섹션 없음.

| 파일 | 등록 전 상태 | 판단 |
|---|---|---|
| `01_compatibility_check.md` | 미등록 | 등록 필요 |
| `02_orin_pyproject_diff.md` | 미등록 | 등록 필요 |
| `03_orin_lerobot_diff.md` | 미등록 | 등록 필요 |
| `04_dgx_lerobot_diff.md` | 미등록 (06 BACKLOG #7 지적 대상) | 등록 필요 |
| `05_datacollector_lerobot_diff.md` | 미등록 (06 BACKLOG #7 지적 대상) | 등록 필요 + 미래 갱신 불요 사유 명시 |
| `check_update_diff.sh` | 미등록 | 등록 필요 |

**`05_datacollector_lerobot_diff.md` 존재 여부**: 파일 실존 확인. 06_dgx_absorbs_datacollector 결정으로 DataCollector 노드가 legacy 이관됐으나, `05_datacollector_lerobot_diff.md` 자체는 삭제되지 않고 역사 기록으로 보존됨. 따라서 색인 등록 + "향후 갱신 불요" 사유 명시가 합리적.

---

## Step 3 — 갱신 내용

`99_lerobot_upstream_Tracking.md` 맨 앞 (Upstream Tracking Log 섹션 이전) 에 "디렉터리 파일 색인" 섹션 신설.

- 디렉터리 내 파일 7건 모두 등록
- `04_dgx_lerobot_diff.md`: 2026-04-28 최초 생성 (`dgx/scripts/smoke_test.sh` 보정 기록), DGX editable install 방식 명시
- `05_datacollector_lerobot_diff.md`: 2026-05-01 최초 생성, 옵션 B (파일 변경 X) 적용, DataCollector legacy 이관으로 향후 갱신 불요 사유 명시
- 등록 현황 노트 서브섹션에 06 BACKLOG #7 → 07 W2 처리 이력 명시

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/lerobot_upstream_check/99_lerobot_upstream_Tracking.md` | M | 디렉터리 파일 색인 섹션 신설 — 파일 7건 전체 등록 |
| `docs/work_flow/specs/BACKLOG.md` | M | 06 BACKLOG #7 → "완료 (07 W2 갱신, 2026-05-03)" 마킹 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (색인 갱신 대상은 `docs/storage/` 영역) ✓
- Coupled File Rule: `orin/lerobot/`, `pyproject.toml` 미변경 → coupled file 갱신 불필요 ✓
- 레퍼런스 활용: 본 todo 는 문서 색인 갱신 — 레퍼런스 참조 불필요 (코드 구현 아님) ✓
- CLAUDE.md 룰 "storage 하위에 bash 명령 예시 추가 X": 색인 섹션에 bash 명령 추가 X ✓

---

## 변경 내용 요약

`99_lerobot_upstream_Tracking.md` 는 upstream commit 추적 로그만 보유하고 있었으며, 디렉터리 내 다른 파일들 (`01~05`, `check_update_diff.sh`) 의 목적과 존재를 설명하는 색인이 없었다. 06_dgx_absorbs_datacollector 사이클 M3 code-tester 가 `04_dgx_lerobot_diff.md`·`05_datacollector_lerobot_diff.md` 색인 누락을 지적 (06 BACKLOG #7) 했으므로, 두 파일 포함 디렉터리 내 전체 파일을 대상으로 "디렉터리 파일 색인" 섹션을 신설했다.

`05_datacollector_lerobot_diff.md` 는 06 결정으로 DataCollector 노드가 legacy 이관됐으므로 향후 갱신 불요임을 색인 설명 및 등록 현황 노트에 명시했다.

---

## code-tester 인계 사항

### 검증 권장 사항

1. **색인 완전성**: `99_lerobot_upstream_Tracking.md` 의 "디렉터리 파일 색인" 테이블이 디렉터리 내 실제 파일 7건 (`01~05 .md`, `check_update_diff.sh`, `99_lerobot_upstream_Tracking.md`) 과 일치하는지 확인

2. **04·05 등록 여부**: `04_dgx_lerobot_diff.md` 와 `05_datacollector_lerobot_diff.md` 두 파일이 색인에 명시 등록됐는지 확인 (06 BACKLOG #7 DOD)

3. **05 legacy 사유 명시**: `05_datacollector_lerobot_diff.md` 항목에 "DataCollector legacy 이관으로 향후 갱신 불요" 사유가 명시됐는지 확인

4. **BACKLOG #7 마킹**: `BACKLOG.md` 06 섹션 #7 항목이 "완료 (07 W2 갱신, 2026-05-03)" 상태인지 확인

5. **bash 명령 예시 미추가**: 색인 섹션에 bash 명령 예시 없음 (CLAUDE.md storage 룰 준수) 확인

6. **diff**: `docs/reference/` 변경 0건 확인
