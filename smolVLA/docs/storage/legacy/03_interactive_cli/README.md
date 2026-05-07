# 03_interactive_cli — Legacy 이관 기록

> 이관 일자: 2026-05-07
> 이관 사유: interactive-cli 동작 이슈로 다음 spec 진입 전 보류 이관
> 후속 결정: 재구현 여부는 추후 spec 에서 별도 결정

---

## 이관 배경

본 디렉터리는 05_interactive_cli 사이클 (그리고 06_dgx_absorbs_datacollector 의 X1·X2 흡수) 에서 구축된 **interactive_cli 자산** 을 보관한다.

이관 시점 (2026-05-07) 에 interactive-cli 가 시연장·SSH·로컬 환경에서 일관되게 동작하지 않는 이슈가 누적되어, 다음 spec 진입 전 자산을 legacy 로 분리하고 활성 노드 (`orin/`, `dgx/`) 에서 제거하기로 결정.

`docs/storage/12_interactive_cli_framework.md`, `13_orin_cli_flow.md`, `14_dgx_cli_flow.md` 도 같은 사유로 동반 이관 (활성 navigator 와의 정합성 유지).

---

## 보관 자산

### 노드별 코드

| 원본 위치 | 이관 위치 |
|---|---|
| `orin/interactive_cli/` | `legacy/03_interactive_cli/orin/` |
| `dgx/interactive_cli/` | `legacy/03_interactive_cli/dgx/` |

각 노드 폴더는 이관 시점 그대로의 구조 (main.sh, README.md, configs/, flows/) 를 유지.

### 설계 문서

| 원본 위치 | 이관 위치 |
|---|---|
| `docs/storage/12_interactive_cli_framework.md` | `legacy/03_interactive_cli/docs_storage_12_interactive_cli_framework.md` |
| `docs/storage/13_orin_cli_flow.md` | `legacy/03_interactive_cli/docs_storage_13_orin_cli_flow.md` |
| `docs/storage/14_dgx_cli_flow.md` | `legacy/03_interactive_cli/docs_storage_14_dgx_cli_flow.md` |

---

## 부수 정리

- `scripts/deploy_dgx.sh`: rsync exclude 라인 `--exclude 'interactive_cli/configs/*.json'` 제거 (디렉터리 부재로 의미 없음).
- `docs/storage/README.md`: 12·13·14 항목을 strikethrough + legacy 이관 표기 (07·10·15 기존 패턴 답습).
- `arm_2week_plan.md`: 플랜 기록 성격이므로 본 이관과 무관하게 유지 (역사적 맥락 보존).
- `docs/work_flow/context/history/` (05·06·08 사이클 기록): read-only 사이클 자료, 손대지 않음.

---

## 후속 결정 (TBD)

본 이관은 *코드/문서를 활성 영역에서 분리* 하는 보류 조치이며, 다음 중 어떤 방향으로 갈지는 별도 spec 에서 결정:

1. **재구현**: 핵심 flow 만 재작성 + 동작 이슈 근본 원인 정리 후 활성화
2. **대체**: 다른 진입점 (예: 단순 셸 스크립트, 또는 직접 명령 호출) 으로 사용자 인터페이스 재구성
3. **폐기**: interactive 진입점 자체를 운영에서 제외, 시연장 운영 매뉴얼 정비

→ 이 결정은 본 README 범위 외이며, 결정 시점에 본 문서에 후속 링크 추가 예정.
