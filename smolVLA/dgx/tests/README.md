# dgx/tests/ — DGX 환경 점검 + 회귀 검증

> 책임: DGX 학습 환경 점검 자산 + 회귀 검증 스크립트 보관. `dgx/scripts/preflight_check.sh` 의 자원 보호 게이트와 보완 관계.
> 신설: 04_infra_setup TODO-X2 (2026-05-01)
> 형제: `orin/tests/` (Orin 측 환경 점검), `dgx/scripts/preflight_check.sh` (DGX 측 학습 전 자원 점검)

---

## 책임 범위

| 범주 | 내용 | 담당 위치 |
|---|---|---|
| 자원 보호 게이트 | OOM / Walking RL 보호 / GPU 점유 점검 | `dgx/scripts/preflight_check.sh` (기존) |
| 환경 점검 | venv / CUDA / lerobot import 검증 | 본 `tests/` |
| 회귀 검증 | 02 산출물 smoke test 재실행 검증 | `dgx/scripts/smoke_test.sh` 재실행 (TODO-X3) |
| 데이터셋 인터페이스 | DataCollector 로부터 수신한 데이터셋 유효성 | 본 `tests/` (TODO-T1 결정 후 추가 예정) |

---

## 자산 (현재)

| 파일 | 책임 | 출처 |
|---|---|---|
| _(비어 있음)_ | — | 04 TODO-X2 에서 디렉터리 신설. 실 스크립트는 TODO-X3 이전 필요 시 추가 |

---

## 자산 (예정 — 04 진행 중 추가)

| 파일 | 책임 | 추가 시점 |
|---|---|---|
| _(TODO-X3 이전 필요 시)_ | 환경 점검 스크립트 | TODO-X3 / TODO-T1 결과에 따라 |

---

## preflight_check.sh 와의 역할 분리

`dgx/scripts/preflight_check.sh` 는 **Walking RL 보호 + OOM 방어** 전용 게이트다. 학습 전 반드시 실행하며 본 `tests/` 와 겹치지 않는다.

```
학습 시작 전 흐름:
  1. source .arm_finetune/bin/activate
  2. bash scripts/preflight_check.sh <시나리오>   # 자원 보호 게이트
  3. (옵션) bash tests/check_env.sh              # 환경 점검 (TODO-X3 이후)
  4. lerobot-train ...
```

---

## 외부 의존성

- `dgx/config/dataset_repos.json` — 학습할 HF 데이터셋 repo_id 목록 (TODO-T1 결정 후 채움)
- `docs/reference/lerobot/` — editable 설치 대상. lerobot-train / lerobot-eval 제공
- `dgx/.arm_finetune/` — 학습 전용 venv (본 tests/ 실행 전 반드시 활성화)

---

## 참고

- `docs/storage/08_dgx_structure.md` §2 (tests/ 컴포넌트 책임) + §3 (마일스톤별 책임 매트릭스)
- `docs/work_flow/specs/04_infra_setup.md` TODO-X2 / TODO-X3 (실 구현·검증)
- `dgx/scripts/preflight_check.sh` — Walking RL 보호 + OOM 방어 게이트 (본 tests/ 와 보완 관계)
