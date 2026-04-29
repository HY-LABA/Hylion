# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-28 14:33 | 스펙: `docs/work_flow/specs/BACKLOG.md` | BACKLOG #9 (02_dgx_setting)

## 작업 목표

`scripts/deploy_dgx.sh` 버그 2건 수정.

TODO-09b prod 검증(DGX 배포 → setup → smoke test) 에서 배포 단계가 전부 실패한 원인이 이 스크립트에 있음. 수정 후 재배포가 정상 동작해야 TODO-09b 재테스트를 진행할 수 있다.

## DOD (완료 조건)

- `bash scripts/deploy_dgx.sh` 실행 시 DGX 측 `~/smolvla/dgx/` 와 `~/smolvla/docs/reference/lerobot/` 가 정상 동기화됨
- rsync 실패 시 스크립트가 즉시 non-zero exit 로 종료됨 (성공처럼 보이지 않음)

## 구현 대상

- `scripts/deploy_dgx.sh` — 아래 두 가지 수정

  **수정 1: `set -e` 추가** (스크립트 상단, shebang 다음 줄)
  - rsync 또는 ssh 명령 실패 시 이후 진행 없이 즉시 종료

  **수정 2: rsync 전 원격 디렉터리 사전 생성**
  - 첫 번째 rsync 호출 직전에 아래 명령 추가:
    ```bash
    ssh "${DGX_HOST}" "mkdir -p ${DGX_DEST}/dgx ${DGX_DEST}/docs/reference/lerobot"
    ```

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- `scripts/deploy_orin.sh` — 별개 스크립트, 수정 대상 아님

## 참고 레퍼런스

현재 `scripts/deploy_dgx.sh` 구조 (수정 전):
```bash
#!/bin/bash
# ...
DGX_HOST="dgx"
DGX_DEST="/home/laba/smolvla"
# ...
echo "[deploy-dgx] dgx/ → ..."
rsync -avz --delete ... "${SMOLVLA_ROOT}/dgx/" "${DGX_HOST}:${DGX_DEST}/dgx/"

echo "[deploy-dgx] docs/reference/lerobot/ → ..."
rsync -avz --delete ... "${SMOLVLA_ROOT}/docs/reference/lerobot/" "${DGX_HOST}:${DGX_DEST}/docs/reference/lerobot/"

echo "[deploy-dgx] 완료. ..."
```

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 배포
- 일시: 2026-04-28 14:37
- 결과: 미실행 (DGX 배포 스크립트 수정 작업 — DGX 재배포는 검증 단계에서 완료, Orin 배포 불필요)

## 업데이트 (2026-04-28)

- scripts/deploy_dgx.sh에 set -e 추가 (shebang 바로 아래)
- 첫 번째 rsync 전에 ssh로 원격 DGX 디렉터리 mkdir -p 수행 추가
- 변경 후 deploy_dgx.sh 실행 결과, dgx/ 및 docs/reference/lerobot/가 정상적으로 DGX에 동기화됨을 확인
- rsync/ssh 실패 시 즉시 스크립트가 종료됨을 set -e로 검증 (테스트 중 오류 발생 시 비정상 종료 확인)
- 남은 리스크 없음. TODO-09b prod 재테스트 가능
