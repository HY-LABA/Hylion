# 20260429_smolvla_test_on_orin
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: Orin 위에서 사전학습된 smolVLA (`lerobot/smolvla_base`) 가 하드웨어와 함께 정상 동작하는지 검증
> 환경: Orin JetPack 6.2 | Python 3.10 | venv `~/smolvla/orin/.hylion_arm`
> 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh orin` → Orin (`laba@ubuntu`)
> Orin 코드 경로: `/home/laba/smolvla/orin/` (rsync 배포 기준)
> 학습 대상: 없음 (추론 전용 검증). 사전학습 가중치 그대로 forward
> 작성: 2026-04-29

---

## 참고 레퍼런스

- `docs/reference/lerobot/src/lerobot/policies/smolvla/` — SmolVLA 정책 구현 (configuration, modeling, processor)
- `docs/reference/lerobot/src/lerobot/robots/bi_so_follower/` — 양팔 SO follower 코드 (TODO-02 양팔 데이터셋 분석 시 참조)
- `docs/reference/lerobot/src/lerobot/teleoperators/bi_so_leader/` — 양팔 SO leader 코드 (TODO-02 양팔 데이터셋 분석 시 참조)
- `docs/reference/seeed-lerobot/src/lerobot/robots/bi_so_follower/` — Seeed fork 양팔 SO follower 코드 (TODO-02 비교 검토)
- `docs/reference/seeed-lerobot/src/lerobot/teleoperators/bi_so_leader/` — Seeed fork 양팔 SO leader 코드 (TODO-02 비교 검토)
- `docs/lerobot_study/03_smolvla_architecture.md` — SmolVLA 일반 구조 (입력 포맷, forward 흐름)
- `docs/lerobot_study/03b_smolvla_milestone_config_guide.md` §2 `03_smolvla_test_on_orin` — 본 마일스톤 config 분기 가이드 (B1 / 모두 기본값 / `compile_model=False`)
- `docs/lerobot_study/04_lerobot_dataset_structure.md` — LeRobotDataset 키 컨벤션 (TODO-02 산출물 작성 기준)
- `docs/lerobot_study/05_hf_model_selection.md` — `lerobot/smolvla_base` 가 본 프로젝트 정책 체크포인트로 확정됨 (TODO-01 가중치 검증 기준)
- `docs/storage/05_orin_venv_setting.md` — Orin venv 구성 (PyTorch JP 6.0 wheel, bf16 지원)
- HuggingFace `lerobot/smolvla_base` 모델 카드 — 사전학습 가중치 출처
- HuggingFace `lerobot/svla_so100_pickplace` 데이터셋 — 사전학습 데이터셋 (TODO-02 단일팔 분석 기준)
- `arm_2week_plan.md` — `03_smolvla_test_on_orin` 마일스톤 정의

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

---

## 본 마일스톤의 위치

`arm_2week_plan.md` 의 03 마일스톤은 **사전학습 smolVLA 가 Orin 에서 하드웨어와 함께 잘 동작하는지 검증** 하는 단계.

- 학습 안 함, 추론만
- 가중치는 `lerobot/smolvla_base` 그대로 사용 (`03b_smolvla_milestone_config_guide.md §2` 의 B1)
- 본 마일스톤의 산출물 (latency / VRAM / 학습 환경 미러링 결과) 은 04~07 의 자원·튜닝 기준선이 된다
- **04_leftarmVLA 와의 차이**: 04 는 SO-ARM 의 배치·시작 각도가 본래 사전학습 분포(`svla_so100_pickplace`) 와 달라지는 단계. 03 은 그 직전 단계로, **가능한 한 사전학습 환경에 가깝게** Orin 추론 환경을 구성해 모델이 의도대로 동작하는지부터 확인한다.

---

## Todo

### [x] TODO-01: `lerobot/smolvla_base` 사전학습 가중치 검증

- 타입: study
- DOD: HuggingFace `lerobot/smolvla_base` 의 모델 카드와 safetensors 의 실제 파라미터 키를 검토하여, **expert layer (action expert) 가중치가 진짜로 포함되어 있음** 을 확인. 학습 흔적(`config.json` 의 `train_expert_only`, `freeze_vision_encoder`, `load_vlm_weights` 등) 을 정리하여 본 모델이 어떤 시나리오(S1~S4) 로 학습되었는지 추정. 본 결과를 `docs/lerobot_study/05_hf_model_selection.md` 와 일관되게 보충 정리.
- 구현 대상:
  - `docs/lerobot_study/07_smolvla_base_weight_inspection.md` — safetensors 키 dump (vlm / expert / state_proj / action_in_proj / action_out_proj 등 카테고리별 파라미터 수), config.json 분석, 학습 시나리오 추정, expert 포함 여부 결론
- 테스트: 없음 (자가 검증 — 문서 작성으로 대체)
- 참조:
  - HuggingFace `lerobot/smolvla_base` (모델 카드, config.json, model.safetensors)
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py` (모듈 구조 — vlm / lm_expert / state_proj / action_in_proj / action_out_proj / action_time_mlp)
  - `docs/lerobot_study/03_smolvla_architecture.md` §A·§B (학습 시나리오 / 가중치 출처)
  - `docs/lerobot_study/05_hf_model_selection.md` §6 (모델 라이선스·재배포)
- 제약: 가중치 파일은 다운로드 후 키만 inspect (전체 파라미터 값은 검토 불필요). 다운로드는 Orin 또는 devPC 어느 쪽이어도 무방하나, 캐시 활용 측면에서 Orin 에서 1회 받아두는 편이 효율적
- 잔여 리스크:
  - 모델 카드에 학습 시나리오 명시가 부족할 가능성 → 그 경우 코드 구조 + 파라미터 수로 추정
  - safetensors 키 dump 결과가 `modeling_smolvla.py` 의 모듈명과 정확히 일치하지 않을 가능성 (HuggingFace 저장 시 prefix 변형) → 키 prefix 매핑 작업 포함

### [x] TODO-02: `svla_so100_pickplace` (단일팔) + 양팔 SO 데이터셋 구조 분석

- 타입: study
- DOD: 본 마일스톤(03) 과 후속 마일스톤(04 / 06) 의 데이터셋 구조 비교를 위한 산출물 작성. **사전학습 분포에 가까운 03 추론 환경의 입력 스펙(카메라 키 개수·이름·해상도, state·action dim, fps, 에피소드 수 등) 확정** 이 핵심 결과물.
- 구현 대상:
  - `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md` — 두 섹션:
    1. **단일팔** (`lerobot/svla_so100_pickplace`) — HuggingFace 데이터셋의 meta.json / info.json / 첫 에피소드 샘플 검토. 카메라 키 개수·이름, image shape, state·action dim, fps, 에피소드 수, 태스크 instruction. 03 추론 환경 입력 스펙의 기준
    2. **양팔** (`docs/reference/lerobot/src/lerobot/robots/bi_so_follower/` + `docs/reference/seeed-lerobot/src/lerobot/robots/bi_so_follower/`) — 두 fork 의 양팔 follower / leader 코드를 비교 검토. 양팔의 state·action dim (12 DOF? 분리 키?), 카메라 키 컨벤션, 데이터셋 키 명명 규칙. 06_biarm_VLA 진입 시 결정해야 할 사항 정리
  - **`empty_cameras` 동작 분석 한 절 포함**: 사전학습 분포(N대) 와 추론 환경 카메라 수(M대) 가 다를 때 `empty_cameras=N-M` 으로 더미 이미지를 채워 forward 가 가능하다는 것은 코드(`configuration_smolvla.py:123-130`, `modeling_smolvla.py:448-449`) 로 확인됨. 다만 **그 상태로 학습이 잘 수렴하는지** 는 03 에서 직접 학습 검증을 못 함 → 04_leftarmVLA 진입 시 검증 항목으로 위임. 본 절은 코드·문헌 분석 수준에서 `smolvla_aloha_sim` (3대 가정 + 더미) 의 선례와 본 프로젝트(2대 / 3대) 의 차이를 정리
- 테스트: 없음
- 참조:
  - HuggingFace `lerobot/svla_so100_pickplace` (단일팔 데이터셋)
  - `docs/reference/lerobot/src/lerobot/robots/bi_so_follower/` + `bi_so_leader/` (양팔 upstream)
  - `docs/reference/seeed-lerobot/src/lerobot/robots/bi_so_follower/` + `bi_so_leader/` (양팔 Seeed fork)
  - `docs/lerobot_study/04_lerobot_dataset_structure.md` (LeRobotDataset 키 컨벤션)
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py:44-49, 123-130` (`resize_imgs_with_padding`, `empty_cameras`)
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py:421-449` (image_features 처리 흐름)
- 제약: 양팔 데이터셋의 경우 HuggingFace Hub 에 본 프로젝트와 동일 구성의 공식 양팔 SO 데이터셋이 없을 수 있음 → 그 경우 코드(robots/teleoperators 의 state/action 정의) 만으로 분석. 추정과 사실 구분하여 기록
- 잔여 리스크:
  - lerobot upstream 과 seeed-lerobot fork 의 양팔 구현 차이가 클 경우 06 결정에 영향 → 차이점을 명시적으로 정리
  - 사전학습 데이터셋 카메라 수 < 04(2대) 일 경우, 04 학습 시 카메라 수 매칭(추가 카메라 입력) 으로 도메인 시프트 발생 → 04 진입 시 트리거할 후속 결정 사항으로 본 문서 §끝에 체크리스트로 남김

### [x] TODO-03: Orin 추론 환경 구성 — 학습 환경 미러링

- 타입: task
- DOD: TODO-02 산출물의 단일팔 데이터셋 입력 스펙(카메라 키 개수·이름·shape, state dim, language instruction) 에 정확히 맞춘 더미 입력 생성기 + smolvla_base 추론 래퍼가 작성됨. `compile_model=False`, `num_steps=10`, `n_action_steps=50` (모두 사전학습 분포에 일치하는 기본값) 로 forward pass 1회 가능.
- 구현 대상:
  - `orin/examples/tutorial/smolvla/inference_baseline.py` — TODO-02 산출물 기반 더미 입력 생성기 + `SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")` 로딩 + `select_action` 1회 호출 + action shape / dtype / range 출력. 기존 `smoke_test.py` (환경 검증) / `load_checkpoint_test.py` (임의 ckpt 호환성 검증) 와 형제 — 본 스크립트는 **사전학습 분포에 미러링된 입력으로 baseline 동작 확인** 이 책임.
- 테스트: 없음 (스크립트 작성 단계 — `python -m py_compile` syntax check 통과. 실 실행 검증은 TODO-05)
- 제약: 카메라 키 이름·개수는 TODO-02 의 `svla_so100_pickplace` 분석 결과를 그대로 사용 (추측 금지). 사전학습 분포와 다른 부분 (예: SO-ARM 시작 각도, 책상 vs 토르소 부착 좌표계) 은 본 마일스톤 범위에서 건드리지 않음 — 그건 04 의 책임.
- 잔여 리스크:
  - `lerobot/smolvla_base` 첫 다운로드 시 네트워크 시간 (Orin 측 기준 5~15분) — TODO-09b / TODO-10b 에서 이미 다운로드되었으면 캐시 재활용
  - language instruction 의 정확한 문자열 — 사전학습 분포와 동일하게 맞춰야 의미 있음 (TODO-02 에서 `single_task` 필드 확인 필요)

### [x] TODO-04: Orin latency / VRAM(UMA) 측정 스크립트 작성

- 타입: task
- DOD: TODO-03 의 inference_baseline.py 를 확장(또는 sibling 스크립트) 하여, warmup N회 + 측정 N회 forward 로 latency 분포(p50 / p95) + RAM(UMA) peak 측정. `num_steps∈{10, 5}` 두 설정 비교. 결과는 JSON 으로 저장하여 후속 분석/문서화 용이하게.
- 구현 대상:
  - `orin/examples/tutorial/smolvla/measure_latency.py` — argparse (`--num-steps`, `--warmup`, `--repeats`, `--output-json`) 지원. `time.perf_counter()` 기반 latency, `psutil` (또는 `tegrastats` 후처리) 으로 RAM peak. `torch.cuda.synchronize()` 호출로 GPU 측정 정확도 보장.
- 테스트: 없음 (스크립트 작성 단계 — `python -m py_compile` syntax check 통과. 실 실행 검증은 TODO-05)
- 제약: TODO-03 완료 후 진행 (입력 미러링 로직 재사용). 측정 자체는 더미 입력이라 호출 패턴만 평가됨 (실제 실시간 제어 latency 와 차이 가능 — 이는 07_biarm_deploy 단계에서 RTC + 실 카메라 입력으로 재측정).
- 잔여 리스크:
  - Orin UMA 메모리는 GPU/CPU 공유라 `torch.cuda.memory_*` 만으로는 부족 — 시스템 메모리(`free -h`) 병행 필요
  - GB10/Orin 의 첫 forward 는 cuDNN benchmark / kernel autotuning 으로 매우 느릴 수 있음 → warmup 회수 충분히 (예: 10회)

### [x] TODO-05: Orin prod 검증 — 측정 + 결과 문서화 (BLOCKED → TODO-06b 로 승계)

- 타입: test
- DOD: TODO-03·04 산출물이 Orin 에서 실제 동작함을 확인. inference_baseline.py forward PASS, measure_latency.py 두 설정(`num_steps=10`, `num_steps=5`) 측정 완료. 결과를 `docs/storage/07_smolvla_base_test_results.md` 로 정리.
- 구현 대상:
  - `docs/storage/07_smolvla_base_test_results.md` — 신규 작성. 형식은 `docs/storage/06_dgx_venv_setting.md` 와 대칭 (절 단위 구성). 포함 내용:
    - §1 본 문서의 위치 (03 마일스톤 prod 검증 결과)
    - §2 추론 환경 미러링 — TODO-02 의 사전학습 데이터셋 입력 스펙과 Orin 추론 환경의 입력 매칭 표
    - §3 inference_baseline.py 실행 결과 (action shape, dtype, range)
    - §4 latency 측정 (`num_steps=10` / `num_steps=5` 비교 표 — p50, p95, RAM peak)
    - §5 04_leftarmVLA 진입 시 자원·튜닝 기준선 (실시간 제어 임계치 대비 latency 여유 / VRAM 여유)
    - §6 잔여 리스크 — 더미 입력 vs 실 카메라 입력 차이, RTC 미평가 (07 단계로 위임)
- 테스트: prod 검증 (Orin 접속 필요)

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료, Orin 측 `~/smolvla/orin/examples/tutorial/smolvla/` 갱신 |
| 2 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` | syntax check 통과 |
| 3 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` | syntax check 통과 |
| 4 | Orin: `ssh orin "ls ~/smolvla/orin/examples/tutorial/smolvla/"` | `inference_baseline.py`, `measure_latency.py` 존재 |

#### 개발자 직접 검증 (대화형, 약 30~60 분 소요)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/inference_baseline.py` | 정책 로드 → forward pass 통과 → action shape (1, 50, *) 출력. exit code 0. 첫 실행 시 HF Hub 다운로드 5~15분 |
| 2 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 10 --warmup 10 --repeats 50 --output-json /tmp/latency_n10.json` | latency p50/p95 + RAM peak 출력, JSON 저장. exit code 0 |
| 3 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 5 --warmup 10 --repeats 50 --output-json /tmp/latency_n5.json` | 동일 형식 결과, num_steps=10 대비 latency 감소 확인 |
| 4 | devPC: `scp orin:/tmp/latency_n10.json /tmp/ && scp orin:/tmp/latency_n5.json /tmp/` | JSON 파일 devPC 로 회수 |
| 5 | devPC: 회수된 JSON 으로 `docs/storage/07_smolvla_base_test_results.md` §3·§4 채움 | 표 완성 |

- 제약: TODO-03·04 완료 후 진행. 첫 forward 는 매우 느릴 수 있으므로 warmup 충분히. Orin UMA 특성상 GPU 메모리 단독 측정 불가 — 시스템 메모리도 함께 기록.
- 잔여 리스크:
  - HF Hub 다운로드 네트워크 변동
  - GB10 capability 12.1 UserWarning 출력 가능 (TODO-09b 와 동일 — 무시 가능)
  - 더미 입력은 실 카메라 분포와 다름 → 본 측정은 "코드 경로 자원 점유" 의 baseline 일 뿐, 실 카메라 입력 latency 는 04 학습 후 별도 검증
- 테스트 결과 기록 (2026-04-29):
  - Codex 비대화형 검증 4단계 전부 PASS
  - 개발자 직접 검증 step 2~5 FAIL: `ModuleNotFoundError: No module named 'orin'`
  - 원인: `inference_baseline.py` / `measure_latency.py` 가 `from orin.lerobot...` 로 임포트 — 본 프로젝트는 `orin/pyproject.toml` 의 `name = "lerobot"` 으로 editable install 되어 있어 `from lerobot...` 으로 임포트해야 정상. 즉 PYTHONPATH 누락이 아니라 임포트 컨벤션 일탈
  - 회귀 grep 결과: `from orin` / `import orin` 패턴은 두 파일(inference_baseline.py · measure_latency.py) 4줄에만 존재. 다른 스크립트(`smoke_test.py` / `using_smolvla_example.py` / `load_checkpoint_test.py`) 는 모두 `from lerobot...` 로 정상
  - 수정 방향: TODO-06 으로 임포트 4줄 수정 + 회귀 방지. `docs/storage/07_smolvla_base_test_results.md` 작성은 TODO-06b 로 위임
  - history: `docs/work_flow/context/history/03_smolvla_test_on_orin/20260429_1454_test_orin_inference_fail.md`
- **마감 (2026-04-29)**: 본 TODO 의 검증 시나리오 + 결과 문서 작성 DOD 는 **TODO-06b 가 그대로 승계**. TODO-06 (임포트 컨벤션 정정) 후 TODO-06b 에서 동일 검증을 PASS 로 재수행하는 흐름. 본 TODO 는 [x] 처리하되 실 검증 통과는 TODO-06b 가 책임.

### [x] TODO-06: `inference_baseline.py` / `measure_latency.py` 임포트 컨벤션 정정

- 타입: task
- DOD: 두 스크립트의 `from orin.lerobot...` 임포트가 본 프로젝트의 editable install 패키지명(`lerobot`) 에 맞게 `from lerobot...` 으로 수정됨. `python -m py_compile` syntax check + `python -c "from ..."` import smoke 통과. 본 변경의 회귀 방지를 위해 `orin/` 하위 전체에서 `from orin` / `import orin` 패턴이 다시 나타나지 않는지 grep 으로 검증.
- 구현 대상:
  - `orin/examples/tutorial/smolvla/inference_baseline.py:2-3` — `from orin.lerobot...` → `from lerobot...` (2줄)
  - `orin/examples/tutorial/smolvla/measure_latency.py:7-8` — `from orin.lerobot...` → `from lerobot...` (2줄)
  - **추가 점검 (의심 신호)**: 두 스크립트의 `obs` 구조가 nested dict (`obs["observation"]["images"]["camera1"]`) 로 되어 있는데 LeRobotDataset 표준은 flat key (`"observation.images.camera1"`). `make_smolvla_pre_post_processors` 입력 포맷 확인 후 필요 시 함께 수정. `docs/lerobot_study/04_lerobot_dataset_structure.md` 와 `docs/reference/lerobot/src/lerobot/policies/smolvla/processor_smolvla.py` 참조
- 테스트: 없음 (스크립트 수정 단계 — `python -m py_compile` syntax check 통과. 실 실행 검증은 TODO-06b)
- 제약: 임포트 라인 외에 비즈니스 로직 변경 금지. nested dict → flat key 수정이 필요하면 그것까지만 (변수명·기능 추가 변경 X). 본 프로젝트의 임포트 컨벤션은 `from lerobot...` 으로 통일되어 있음 (`smoke_test.py`, `using_smolvla_example.py`, `load_checkpoint_test.py` 모두 동일 패턴 — `setup_env.sh:77` 의 `pip install -e ${SMOLVLA_DIR}[smolvla,hardware,feetech]` 로 editable 등록됨).
- 잔여 리스크:
  - `make_smolvla_pre_post_processors` 입력 포맷이 nested dict 를 받지 않을 가능성 — 그 경우 처리 코드도 수정 필요 (TODO-06 범위 안)
  - `processor_smolvla.py` 의 입력 키 컨벤션이 `OBS_IMAGES.<name>` flat 인 점 ([04_lerobot_dataset_structure.md](../../lerobot_study/04_lerobot_dataset_structure.md)) — TODO-06 작업 시 이를 기준으로 정정
- **완료 (2026-04-29 15:19)**: 사전 점검에서 두 스크립트가 임포트뿐 아니라 obs 구조 / 헬퍼 사용 / 카메라 키 처리 전반이 모델 forward 의 기대와 어긋남을 확인 — 사용자 승인 후 두 파일을 `smoke_test.py` 패턴으로 전면 재작성. 주요 변경:
  - 임포트: `from orin.lerobot...` → `from lerobot.policies.smolvla import SmolVLAPolicy` / `from lerobot.policies import make_pre_post_processors` / `from lerobot.policies.utils import prepare_observation_for_inference` (3건 모두 `orin/lerobot/` 에 export 확인)
  - 카메라 키 / state dim 하드코딩 제거 → `policy.config.input_features` 에서 자동 추출 (사전학습 분포 미러링)
  - obs 구조: nested dict → flat key (`modeling_smolvla.py:486` 의 `batch[OBS_STATE]` 접근 패턴 일치)
  - 처리 헬퍼: `make_smolvla_pre_post_processors` 직접 → `make_pre_post_processors(policy.config, pretrained_path=MODEL_ID, ...)` factory 로 사전학습 normalization stats 로드
  - obs 전처리: 직접 cuda tensor → `prepare_observation_for_inference` 로 (H,W,C) uint8 → (1,C,H,W) float32 + task/robot_type 키 자동 추가
  - `measure_latency.py`: `policy.config.num_steps = args.num_steps` 로 flow matching steps override, JSON 키 단위 명시화 (`latency_p50_s` 등)
  - 검증: `py_compile` PASS (2건), 회귀 grep `^from orin|^import orin` 0건, 임포트 심볼 export 3건 모두 확인. devPC PyTorch 미설치로 실 import smoke 는 미수행 — TODO-06b 에서 prod 검증
  - history: `docs/work_flow/context/history/03_smolvla_test_on_orin/20260429_1519_task_import_convention_rewrite.md`

### [x] TODO-06b: TODO-05 재실행 + 결과 문서 작성

- 타입: test
- DOD: TODO-06 수정 산출물이 Orin 에서 동작함을 확인. TODO-05 의 개발자 직접 검증 step 1~5 PASS, latency JSON 회수, `docs/storage/07_smolvla_base_test_results.md` §1~§6 작성 완료.
  - ※ DOD 정정 (2026-04-29): action shape 기대값 `(1, 50, *)` → `(1, action_dim)` (`(1, 6)`). `select_action` 은 chunk queue 에서 dequeue 된 단일 action 을 반환하는 lerobot 표준 API 동작이며 `(1, 6)` 출력은 정상. `(1, 50, *)` 는 raw `forward()` 의 chunk shape 로 DOD 에 혼용된 오기였음.
- 구현 대상:
  - `docs/storage/07_smolvla_base_test_results.md` — TODO-05 구현 대상과 동일 (§1~§6)
- 테스트: prod 검증 (Orin 접속 필요)

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` | syntax check 통과 |
| 2 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` | syntax check 통과 |
| 3 | devPC: `grep -rn "from orin\|import orin" orin/` | 검색 결과 없음 (회귀 방지 확인) |
| 4 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료 |
| 5 | Orin: `~/smolvla/orin/.hylion_arm/bin/python -c "from lerobot.policies.smolvla import SmolVLAPolicy, make_smolvla_pre_post_processors; print('OK')"` | `OK` 출력 |

#### 개발자 직접 검증 (대화형, 약 30~60 분 소요)

TODO-05 의 "개발자 직접 검증" 표 step 1~5 를 그대로 재실행한 뒤, 추가로:

| # | 단계 | 기대 결과 |
|---|---|---|
| 6 | devPC: 회수된 JSON + inference_baseline 출력으로 `docs/storage/07_smolvla_base_test_results.md` 작성 | §1~§6 완성 |

- 제약: TODO-06 완료 후 진행. 첫 forward 시 HF Hub 다운로드 5~15분 가능 (이미 받았으면 재사용)
- 잔여 리스크: TODO-05 와 동일 — HF Hub 네트워크 변동, GB10 capability 12.1 UserWarning (무시 가능)
- 테스트 결과 기록 (2026-04-29):
  - Codex 검증 step 1~4 PASS, step 5 FAIL (`libcusparseLt.so.0` ImportError — `source activate` 없이 venv python 직접 실행 시 CUDA 라이브러리 경로 미설정. activate 후 import OK 확인)
  - 개발자 검증 step 1,3,5 PASS / step 2,4 PARTIAL
  - DOD 1 PASS (정정): `inference_baseline.py` exit 0, action shape `(1, 6)` = `(1, action_dim)` — `select_action` 의 정상 반환 shape. DOD 기대값 `(1, 50, *)` 는 raw `forward()` chunk shape 로 오기였음 (2026-04-29 정정)
  - DOD 3 PARTIAL: `latency_n5.json` 저장, exit 0. 단 num_steps=5 p50 5.59ms = num_steps=10 p50 5.59ms (동일) — latency 감소 미확인. num_steps override 미적용 또는 해당 범위 측정 노이즈 내 가능성
  - `docs/storage/07_smolvla_base_test_results.md` 신규 작성 완료 (§1~§6, 불일치 2건을 잔여 리스크로 기록)
  - history: `docs/work_flow/context/history/03_smolvla_test_on_orin/20260429_1550_test_todo06b_partial.md`

### [x] TODO-07: 실 SO-ARM hardware-in-the-loop 추론 스크립트 작성

- 타입: task
- DOD: Orin 에 follower SO-ARM 1대 + 카메라 2대 (사전학습 분포 `svla_so100_pickplace` 의 `top + wrist` 와 동일) 가 연결된 환경에서, smolvla_base 가 매 step **실 카메라 프레임 + 실 follower joint state** 를 받아 forward → action chunk 출력 → (모드별로) 실 follower 에 송신하는 스크립트 작성. **dry-run / 실 송신 두 모드 지원**. 실행은 TODO-07b 에서 수행.
- 구현 대상:
  - `orin/examples/tutorial/smolvla/hil_inference.py` — `--mode {dry-run,live}`, `--cameras top,wrist`, `--n-action-steps 5` (안전을 위해 기본값을 50→5 로 축소), `--max-steps 100` (전체 실행 step 상한). dry-run 은 action 을 stdout/JSON 으로 dump 만, live 는 follower 에 송신
  - lerobot 의 카메라/로봇 API 는 `using_smolvla_example.py` 의 패턴 (`from lerobot.cameras.opencv import OpenCVCameraConfig`, `from lerobot.robots.so_follower import SO100Follower, SO100FollowerConfig`) 그대로 재사용. 신규 robot 클래스 / 카메라 클래스 작성 X (CLAUDE.md 의 "레퍼런스에 없는 새 코드는 사용자 확인 후" 원칙 준수)
- 안전 장치 (3가지 조합):
  - **(i) 모터 토크 한계**: `SO100Follower` 의 기본 토크 한계에 의존 (lerobot teleoperate 와 동일). 별도 코드 추가 X
  - **(ii) action 클램프**: 본 마일스톤에서는 미적용 (모터 토크 한계 + 짧은 송신으로 충분). 04 진입 시 데이터 분포 기반 클램프 도입 검토 — Backlog 로 등록
  - **(iii) chunk 짧게 끊기**: `n_action_steps=5` (chunk_size=50 의 1/10). 폭주 시 영향 시간 대폭 축소. 5 step 후 다음 forward 까지 대기 (또는 즉시 다음 forward — TODO-07b 에서 결정)
- 테스트: 없음 (스크립트 작성 단계 — `python -m py_compile` syntax check 통과. 실 실행 검증은 TODO-07b)
- 제약: TODO-06b 완료 후 진행 (forward 동작 검증된 상태에서 hardware 추가). 카메라 키 이름은 TODO-02 의 `svla_so100_pickplace` 분석 결과(`top` / `wrist` 또는 그 변형) 와 정확히 일치시켜야 함 — 추측 금지. 사전학습 분포와 다른 환경/배치에서 의미 있는 태스크 수행은 기대 안 함 (그건 04 의 책임).
- 잔여 리스크:
  - 사전학습 분포(`svla_so100_pickplace` = lego 큐브 pick-and-place) 와 본 프로젝트 책상 환경/배치/시작 각도가 다름 → action 이 큰 값을 뱉을 수 있음. 안전 장치 (i)+(iii) 로 대응
  - 카메라 키 이름이 TODO-02 분석 결과와 다를 경우 forward 실패 → TODO-07b 첫 단계로 dry-run 검증
  - SO-ARM USB 포트 번호가 연결 순서로 바뀌는 BACKLOG 01_teleoptest #1 이슈 — TODO-07b 실행 전 `lerobot-find-port` 로 재확인
- **완료 (2026-04-29 15:31)**: 사전 점검 4단계 (TODO-02 산출물 검토 / `using_smolvla_example.py` API 패턴 정독 / `SO100Follower`·`OpenCVCameraConfig` 시그니처 확인 / 헬퍼 시그니처 확인) 후 사용자 승인으로 신규 파일 1개 작성. 핵심 결정:
  - **카메라 키 매핑 전략 A**: hil_inference.py 안에서 직접 dict key 를 `camera1/camera2` 로 생성 (processor rename 의존 X)
  - **임의 고정**: `top → camera1`, `wrist → camera2` (argparse `--cameras top:0,wrist:1`)
  - **`empty_cameras=1` runtime 설정**: smolvla_base 가 3대 입력 기대, 추론 환경 2대 → 1슬롯 더미(mask=0) 처리. `policy.config.empty_cameras = 1` 로 모델 forward 자동 처리 ([modeling_smolvla.py:421-449](../../docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py))
  - **안전 장치 (i)+(iii)**: SO100Follower 기본 토크 한계 의존 + `policy.config.n_action_steps = 5` runtime override
  - **추가 안전**: SIGINT 핸들러 + try/finally `robot.disconnect()` — Ctrl+C 시 시리얼 통신 충돌 회피, 어떤 종료 경로로든 모터 토크 enable 상태 방치 방지
  - **API 재사용**: `using_smolvla_example.py` 패턴 그대로 — `OpenCVCameraConfig` / `SO100Follower(Config)` / `build_inference_frame` / `make_robot_action` / `hw_to_dataset_features`. 신규 robot/camera 클래스 작성 X
  - 검증: `py_compile` PASS, 회귀 grep `^from orin|^import orin` 0건 유지, 임포트 심볼 export 5건 + 모듈 직접 경로 import 2건 모두 확인. devPC PyTorch 미설치로 실 import smoke 는 미수행 — TODO-07b 에서 prod 검증
  - history: `docs/work_flow/context/history/03_smolvla_test_on_orin/20260429_1531_task_hil_inference.md`

### [x] TODO-07b: TODO-07 prod 검증 — Orin + SO-ARM 실 동작

- 타입: test
- DOD: TODO-07 의 hil_inference.py 가 Orin + 실 follower SO-ARM 1대 + 카메라 2대(top + wrist) 환경에서 dry-run PASS → live 모드에서 팔 동작 + 안전 (충돌·관절 한계 위반 없음) 관찰. 결과를 `docs/storage/07_smolvla_base_test_results.md` 에 §7 추가.
- 구현 대상:
  - `docs/storage/07_smolvla_base_test_results.md` §7 — hardware-in-the-loop 검증 결과:
    - 7.1 환경 (follower 포트, 카메라 디바이스, 카메라 키 매핑)
    - 7.2 dry-run 결과 (action shape / dtype / range / 첫 5 step action 값 dump)
    - 7.3 live 결과 (팔 동작 여부, 송신된 action step 수, 관절 한계 위반 횟수, 비상정지 발동 여부)
    - 7.4 사전학습 분포 미스매치 관찰 (예상되는 행동 vs 실제 행동 — 정성 기록)
- 테스트: prod 검증 (Orin + SO-ARM follower 1대 + 카메라 2대 연결 필요)

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/hil_inference.py` | syntax check 통과 |
| 2 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료 |
| 3 | Orin: `ssh orin "ls ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py"` | 파일 존재 |

#### 개발자 직접 검증 (대화형, 약 60~90 분 소요)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | Orin: SO-ARM follower 1대 + 카메라 2대 연결, `lerobot-find-port` 로 follower 포트 확인 | `/dev/ttyACM*` 식별 |
| 2 | Orin: `python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py --mode dry-run --cameras top,wrist --max-steps 5 --output-json /tmp/hil_dryrun.json` | dry-run 모드 진입, action shape/range 출력, JSON 저장. exit code 0. **팔 미동작** |
| 3 | dry-run JSON 의 action range 검토 — 비정상적으로 큰 값 (절댓값 > 학습 분포 95%ile 추정값) 없는지 확인 | 정상 범위 |
| 4 | Orin: 비상정지 절차 숙지 (Ctrl+C / 전원 차단 / 팔 물리적 제동). `python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py --mode live --cameras top,wrist --n-action-steps 5 --max-steps 5` | live 모드 진입, 5 step (= 1회 forward × 5 action) 송신 후 종료. **팔이 짧게 움직이고 멈춤** |
| 5 | step 4 동안 관절 한계 / 충돌 / 비정상 음 (모터 과전류) 발생 여부 관찰 | 미발생 |
| 6 | step 4 가 정상이면 `--max-steps 50` 으로 재실행 (10회 forward = 50 step) | 팔 동작 지속, 안전 유지 |
| 7 | 결과를 `docs/storage/07_smolvla_base_test_results.md` §7 로 작성 | 7.1~7.4 채움 |

- 제약: TODO-07 완료 후 진행. **step 4 시작 전 비상정지 절차 반드시 숙지** (Ctrl+C 후에도 팔이 잠시 움직일 수 있음 — 손이 닿지 않는 위치에서 시작). 카메라가 SO-ARM 작업 영역과 일관되게 배치되어 있어야 의미 있는 forward 가능
- 잔여 리스크:
  - 사전학습 환경(책상 mount + lego 큐브) 과 본 프로젝트 환경(연구실 책상, 큐브 없을 가능성) 차이로 action 이 의도되지 않은 방향으로 갈 수 있음 — `n_action_steps=5` 로 영향 시간 최소화
  - 첫 live 실행은 안전을 위해 작업 영역에 장애물 없는 빈 공간에서 시도
  - 본 검증의 목적은 "**파이프라인이 hardware 까지 이어져서 동작**" 의 확인이지 "**태스크 성공**" 이 아님 — 정성 기록 위주
- 완료 (2026-04-29):
  - Codex 검증 4단계 전부 PASS
  - 개발자 직접 검증 9단계 전부 PASS
  - DOD 1~5 모두 충족 — dry-run 5 step PASS, action max_abs=2.2929 정상, live 5 step + live 50 step 팔 동작 확인, 안전 이상 없음
  - 실행 확정 인자: `--follower-port /dev/ttyACM1 --cameras top:2,wrist:0 --flip-cameras wrist` (`lerobot-find-cameras opencv` 로 재발견 필요했음)
  - 팔이 calibration 중간값 근처에서 경직: 사전학습 분포 미스매치 예상 동작, 04_leftarmVLA 학습으로 해결 필요
  - `docs/storage/07_smolvla_base_test_results.md` §7 (7.1~7.5) 작성 완료
  - history: `docs/work_flow/context/history/03_smolvla_test_on_orin/20260429_1641_test_todo07b_pass.md`

---

> Backlog → [docs/work_flow/specs/BACKLOG.md](BACKLOG.md) 에 본 스펙 섹션을 추가하여 운영
