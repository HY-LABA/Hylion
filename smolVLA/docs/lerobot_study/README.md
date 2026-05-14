# lerobot_study — lerobot upstream + SmolVLA 스터디 노트

> 기준 레퍼런스: `docs/reference/lerobot/` (v0.5.1)
> 목적: lerobot 레포 구조 · SmolVLA 정책 아키텍처를 코드 레벨에서 정리한 read-only 스터디 자료. **upstream 사실 위주** — 프로젝트 결정·적용은 별도 위치에 분리.

## 인덱스

| # | 파일 | 내용 |
|---|---|---|
| 00 | [00_lerobot_repo_overview.md](00_lerobot_repo_overview.md) | lerobot v0.5.1 레포 전체 개요 (디렉토리 구조 · 빌드 시스템 · 워크플로우 명령) |
| 01 | [01_lerobot_root_structure.md](01_lerobot_root_structure.md) | 루트 디렉토리 트리 (`src/`·`tests/`·`examples/`·`docs/` 등) |
| 02 | [02_lerobot_src_structure.md](02_lerobot_src_structure.md) | `src/lerobot/` 모듈별 역할 (policies · datasets · scripts · utils 등) |
| 03 | [03_smolvla_architecture.md](03_smolvla_architecture.md) | SmolVLA 정책 아키텍처 · config 분기점 (어느 플래그가 무엇을 의미하나) |

## 분리된 문서

upstream snapshot 이 아닌 프로젝트 결정·적용 문서는 다음 위치로 이관:

- `docs/storage/11_smolvla_model_decision.md` — SmolVLA 모델 선정 결정 (구 `05_hf_model_selection.md`)
- `docs/storage/lerobot_upstream_check/05_so100_vs_so101.md` — SO-100 vs SO-101 정합 결정 (구 `06_so100_vs_so101.md`)

## 작성 이력

- 2026-04-27: 00 · 01 · 02 · 03 · 04 · 05 초안
- 2026-05-04: SO-100 vs SO-101 분석 작성 (당시 `08_` 번호)
- 2026-05-12: 정리 사이클
  - 삭제 (6건): 파인튜닝 가능성 · base 가중치 · 사전학습 데이터셋 · base 테스트 결과 · 마일스톤 config 가이드 · `04_lerobot_dataset_structure` (현 단계 학습 수준 초과)
  - 이관 (2건): 모델 선정 → `docs/storage/`, SO-100 vs SO-101 → `docs/storage/lerobot_upstream_check/`
  - 정화: 00 · 02 · 03 에서 "본 프로젝트", "우리 것", "TODO-NN" 류 프로젝트 마커 제거
