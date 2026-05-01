# TODO-X1 작업 history — dgx/ 구조·기능 책임 매트릭스 + 마이그레이션 계획

> 작성: 2026-05-01 09:00 | task-executor

## 요약

TODO-X1 (study 타입) 완료. `docs/storage/08_dgx_structure.md` 신규 작성.

## 주요 발견 / 결정

1. **DGX 는 pyproject.toml 미존재** — upstream lerobot editable 설치 그대로 사용. Category B 변경 (`dgx/pyproject.toml`) 은 본 TODO 에서 해당 없음.
2. **dgx/lerobot/ curated 디렉터리 미존재** — orin/ 과 달리 코드 트리밍 불필요. upstream 무수정 원칙 유지.
3. **run_teleoperate.sh → DataCollector (후보 a 채택)**: DGX 는 SO-ARM 직접 연결 없음 → teleop 불가. DataCollector 가 책임 주체. 최종 이동은 TODO-D2 시점.
4. **04_dgx_lerobot_diff.md 존재 확인** — 02 마일스톤 산출물로 이미 생성됨. 본 TODO 에서 추가 이력 없음 (코드 변경 없음).
5. **DataCollector ↔ DGX 인터페이스 미결** — TODO-T1 awaits_user 답 대기. §5-3 config/dataset_repos.json 스키마는 T1 결정 후 갱신 필요.

## 산출물

- `docs/storage/08_dgx_structure.md` (신규) — §0~§6 + 변경 이력
- `docs/work_flow/context/todos/X1/01_implementation.md` (신규)

## 다음 단계

- TODO-X2 (마이그레이션 실행): §5 마이그레이션 계획 기반. tests/, config/ 신규 2건 + README.md 갱신
- TODO-T1 (데이터 전송 방식): awaits_user. 결정 후 §5-3 스키마 갱신
