# 04. DGX lerobot 실행 래퍼 변경 이력

> 목적: DGX Spark 학습 검증에서 upstream lerobot 동작을 직접 수정하지 않고, `dgx/` 래퍼와 실행 스크립트로 보정한 변경 사항을 누적 기록한다.
> upstream 기준 commit: `ba27aab79c731a6b503b2dbdd4c601e78e285048` (v0.5.1-42, 2026-04-22 동기화)
>
> 원칙: `docs/reference/lerobot/` upstream submodule은 읽기 전용이다. DGX에서 lerobot 학습 CLI 실행에 필요한 보정은 `dgx/` 아래 스크립트로만 수행한다.

---

## 현재 차이 요약

DGX는 upstream lerobot 코드를 복사하거나 수정하지 않는다. `scripts/deploy_dgx.sh`가 upstream submodule을 DGX의 `~/smolvla/docs/reference/lerobot/`로 동기화하고, DGX 전용 가상환경에서 editable install로 사용한다.

| 구분 | upstream lerobot | DGX 보정 위치 |
|---|---|---|
| 학습 CLI | `lerobot-train` 기본 동작 | `dgx/scripts/smoke_test.sh`에서 smoke test용 인자와 환경 준비 |
| 환경 격리 | upstream 외부 책임 | `dgx/scripts/setup_train_env.sh`, `dgx/scripts/preflight_check.sh` |
| 자원 측정 | upstream 외부 책임 | `dgx/scripts/smoke_test.sh`의 `nvidia-smi`/`free -m` 샘플링 |

---

## 변경 이력

### [2026-04-28] `dgx/scripts/smoke_test.sh` — DGX 1-step smoke test prod 보정

**대상 파일:** `dgx/scripts/smoke_test.sh`

**변경 내용:**

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| venv 활성화 순서 | preflight 실행 후 venv 활성화 | venv 활성화 후 preflight 실행 |
| output dir 처리 | resource sample log를 `output_dir` 안에 만들면서 lerobot output dir을 선생성 | lerobot output dir은 선생성하지 않고, resource sample은 별도 `outputs/resource_samples/`에 저장 |
| Hub 업로드 | upstream policy config 기본값 영향으로 `policy.repo_id` 요구 | smoke test에서 Hub push 비활성화 |
| 카메라 feature 이름 | dataset `top`/`wrist`와 policy `camera1`/`camera2`/`camera3` 불일치 | smoke test용 rename map으로 `top -> camera1`, `wrist -> camera2` 매핑 |
| loss 출력 | 1 step에서 기본 log 주기 때문에 loss가 stdout에 출력되지 않을 수 있음 | log 주기를 1로 설정 |
| 자원 샘플링 | 5초 간격, GB10 UMA memory `[N/A]` 처리 미흡 | 1초 간격, GPU memory N/A와 system RAM peak를 구분 출력 |

**변경 이유:**

TODO-09b DGX prod 검증에서 `smoke_test.sh` 단독 실행을 완료 조건으로 삼았다. 실제 DGX 실행 중 다음 문제가 확인되어, upstream lerobot을 직접 수정하지 않고 DGX wrapper 레벨에서 보정했다.

- preflight가 venv/HF_HOME/CUDA_VISIBLE_DEVICES 설정 전에 실행되어 실패
- resource sample 로그를 쓰기 위해 lerobot output dir을 먼저 만들면서 `resume=false` 검증에 실패
- SmolVLA policy의 `push_to_hub` 기본값 때문에 smoke test에도 `policy.repo_id`가 요구됨
- `lerobot/svla_so100_pickplace` dataset camera key와 pretrained `lerobot/smolvla_base` policy camera key가 달라 feature mismatch 발생
- 1-step smoke test에서 loss와 GB10 UMA 자원 지표가 결과 기록에 충분히 드러나지 않음

**영향 범위:**

| 기능 | 영향 |
|---|---|
| DGX 1-step smoke test | 단독 실행 가능. 최종 prod 검증 PASS |
| upstream lerobot 코드 | 변경 없음 |
| Orin inference path | 영향 없음 |
| 장시간 DGX 학습 | 직접 변경 없음. smoke test용 인자(`steps=1`, `batch_size=8`, `save_checkpoint=false`)에 한정 |
| HF Hub 업로드 | smoke test에서는 비활성화. 실제 학습 업로드 정책은 별도 학습 명령에서 결정 |

**검증 결과:**

| 검증 항목 | 결과 |
|---|---|
| 로컬 syntax check | PASS |
| DGX 배포본 syntax check | PASS |
| DGX preflight smoke | PASS |
| DGX `lerobot-train` 1 step | PASS, exit code 0 |
| 최종 loss | `0.545` |
| train step time | `5.97s/step` |
| 전체 smoke 소요 | `48초` |
| GPU util peak | `90%` |
| GPU mem peak | `N/A (GB10 UMA)` |
| System RAM used peak | `48226 MiB` |

**후속 기록:**

- `docs/work_flow/context/current_test.md` 개발자 직접 검증 #3/#4에 결과와 중간 보정 원인을 기록했다.
- `docs/lerobot_study/06_smolvla_finetune_feasibility.md §5.2`에 GB10 smoke test 실측값을 반영했다.

---

## upstream 동기화 시 재확인 항목

- [ ] `SmolVLAConfig.push_to_hub` 기본값 또는 train config validation이 바뀌었는지 확인
- [ ] `lerobot/smolvla_base` policy의 expected visual feature 이름이 바뀌었는지 확인
- [ ] `lerobot/svla_so100_pickplace` dataset camera key가 바뀌었는지 확인
- [ ] `lerobot-train` output dir 존재 검증 정책이 바뀌었는지 확인
- [ ] GB10 UMA에서 `nvidia-smi` memory field가 계속 `[N/A]`인지 확인
