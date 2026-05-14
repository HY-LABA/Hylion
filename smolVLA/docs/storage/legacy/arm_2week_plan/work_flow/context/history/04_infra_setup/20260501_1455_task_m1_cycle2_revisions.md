# TODO-M1 cycle 2 수정 기록

> 작성: 2026-05-01 14:55 | task-executor | cycle: 2

## 개요

code-tester cycle 1 MAJOR_REVISIONS 발급 (Critical #1, #2) 에 대한 수정.

## Critical #1 — BACKLOG.md [04_infra_setup] #6 신규 추가

- 파일: `docs/work_flow/specs/BACKLOG.md`
- 변경: [04_infra_setup] 섹션 #5 행 뒤에 #6 행 추가
- 내용: 시연장 미러링 자동 검증 스크립트 항목. 우선순위 낮음 (05·06 트리거 시 중간), 상태 미완.

## Critical #2 — §5 lerobot-record dry-run 추측 CLI 교체

- 파일: `docs/storage/11_demo_site_mirroring.md`
- 변경: §5 소프트웨어 게이트의 lerobot-record dry-run bash 블록 → 옵션 B 추상 기술로 교체
- 제거된 추측 플래그: `--robot-path`, `--cameras top,wrist`, `--num-episodes`, `--num-frames`, `--dry-run`
- 교체 내용: draccus dataclass 방식 안내 + 구체 호출은 TODO-D3 prod 검증 시점으로 이관

## 변경 파일

| 파일 | 변경 종류 |
|---|---|
| `docs/work_flow/specs/BACKLOG.md` | M — [04_infra_setup] #6 행 추가 |
| `docs/storage/11_demo_site_mirroring.md` | M — §5 lerobot-record dry-run 교체 + §7 변경 이력 추가 |
