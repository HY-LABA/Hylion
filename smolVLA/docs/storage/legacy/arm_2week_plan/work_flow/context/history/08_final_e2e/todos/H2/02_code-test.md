# TODO-H2 — Code Test

> 작성: 2026-05-04 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 1건.

## 단위 테스트 결과

```
pytest 대상 없음 — H2 변경 파일은 마크다운 문서 2건 (docs/storage/02_hardware.md, docs/work_flow/specs/BACKLOG.md).
코드 변경 없음 (DOD 정당성 판단: 분기 불필요 결론).

pytest 자체: devPC 에 pytest 미설치 — 마크다운 전용 변경이므로 단위 테스트 비적용.
```

## Lint·Type 결과

```
ruff check docs/storage/02_hardware.md docs/work_flow/specs/BACKLOG.md
→ warning: No Python files found — All checks passed! (마크다운 파일 ruff 대상 외)

mypy 대상 없음 (Python 코드 변경 없음).
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. dgx/record.py `--robot.cameras` 분기 불요 결정 정당성 (둘 다 640×480 MJPG) | ✅ | 01_implementation.md §1 + §9-2 에 근거 명시. U20CAM-720P 640×480/MJPG 지원, OV5648 동일. 현재 record.py 이미 MJPG 강제 적용 중 — 추가 분기 불요 결론 논리적으로 타당. |
| 2. orin/config/cameras.json slot 별 분기 불요 정당성 | ✅ | cameras.json 은 index+flip 만 저장. hil_inference.py 는 width=640/height=480/fps=30 하드코딩. U20CAM-720P 640×480@30fps 지원. 분기 불요 결론 타당. |
| 3. hil_inference.py flip 기본값 변경 불요 정당성 | ✅ | 기본값 `set()` (플립 없음) 유지 — 물리 장착 방향은 시연장 셋업 C1 시 결정 후 cameras.json 또는 --flip-cameras 로 적용. BACKLOG #2 에 추적 등록됨. 논리 타당. |
| 4. §5-2 fourcc=MJPG 패턴 두 카메라 모두 적용 가능 확인 | ✅ | 02_hardware.md §9-2 표에 "둘 다 640×480 + MJPG 적용 중" 명시. DGX record.py 이미 fourcc=MJPG 강제 — 추가 변경 불필요 확인됨. |
| 5. 광각 wrist 분포 차이 BACKLOG 신규 (#1) | ✅ | BACKLOG.md 08_final_e2e 섹션 항목 #1: "wrist 광각 (FOV-H 102°) 와 smolvla_base 사전학습 분포 차이" 등록. 03 BACKLOG #11 연계 명시. |
| 6. wrist flip 미결 BACKLOG 신규 (#2) | ✅ | BACKLOG.md 08_final_e2e 섹션 항목 #2: "wrist 카메라 장착 방향 flip 미결" 등록. 03 BACKLOG #16 연계 명시. |
| 7. H1 Recommended 흡수 — §7 수량 "2대" → "1대" 갱신 | ✅ | 02_hardware.md §7 수량: "1대 (overview, SO-ARM 관측용)" 확인. 이전 "2대" 표기 완전 제거. grep 결과: "Camera: 2대" 없음. |
| 8. (보너스) DGX record.py vs Orin 카메라 키 불일치 보고 | ✅ | 01_implementation.md §5 + 02_hardware.md §9-1 에 `wrist_left`/`overview` vs `top`/`wrist` 불일치 상세 기술. 09 사이클 검토 권장 명시됨. BACKLOG 또는 ANOMALIES 별도 등록은 없으나 §9-1/§9-2 에 충분히 문서화됨. |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/work_flow/specs/BACKLOG.md` 08_final_e2e 섹션 | DGX record.py 카메라 키 불일치(`wrist_left`/`overview` vs `top`/`wrist`) 가 §9-1 문서에는 있으나 BACKLOG 항목으로는 미등록. 잠재 영향(C2 수집 데이터셋 키 → T1 fine-tune 키 매핑 불일치 가능성)이 있으므로 BACKLOG #3 으로 추가 등록 검토 권장. 단 §9 문서화로 추적 가능 상태이므로 Critical 해당 없음. |

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/ 미변경. |
| B (자동 재시도 X 영역) | ✅ | orin/lerobot/, dgx/lerobot/, pyproject.toml, deploy_*.sh, .gitignore 미변경. |
| Coupled File Rules | ✅ | pyproject.toml·orin/lerobot/ 미변경 — Coupled 파일 갱신 불필요. |
| 옛 룰 | ✅ | docs/storage/ 하위 bash 명령 예시 추가 없음 (§9 는 설명 표 + 리스크 기술만). |

## 검증 명령 실행 결과

```
grep -c "1대.*overview" docs/storage/02_hardware.md         → 1  (기대: ≥1) ✅
grep "Camera: 2대" docs/storage/02_hardware.md              → 없음 ✅
grep -c "^## 9" docs/storage/02_hardware.md                 → 1  (§9 신규 섹션) ✅
grep -c "^## \[08_final_e2e\]" BACKLOG.md                   → 1  ✅
grep -c "wrist 광각|wrist flip|wrist 카메라 장착 방향" BACKLOG.md → 3  (≥2) ✅
git diff --stat record.py cameras.json hil_inference.py     → H2 변경 아님 확인:
  record.py 변경은 N1(뒤로가기 UX) 산출물, hil_inference.py 변경은 R2(SO101 마이그레이션) 산출물.
  H2 task-executor 는 코드 변경 0 선언 — 정합.
```

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

H2 변경 영역은 마크다운 문서 2건만이며 코드 변경 없음. 문서 정합성 확인 완료. DOD 8항목 전항 충족. Critical 0건.
