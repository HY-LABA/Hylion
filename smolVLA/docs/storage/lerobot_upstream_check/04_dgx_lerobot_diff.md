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

---

### [2026-05-01] `dgx/tests/`, `dgx/config/` 신규 디렉터리 — 04 TODO-X2 마이그레이션

**대상 파일:**
- `dgx/tests/README.md` (신규)
- `dgx/config/README.md` (신규)
- `dgx/config/dataset_repos.json` (신규 — placeholder)
- `dgx/README.md` (갱신 — pyproject.toml 미존재 주의사항 + DataCollector 인터페이스 + 새 디렉터리 안내)

**변경 내용:**

| 항목 | 내용 |
|---|---|
| `dgx/tests/` 신규 | DGX 측 환경 점검 + 회귀 검증 자산 보관 디렉터리. 실 스크립트는 TODO-X3 이전 필요 시 추가 |
| `dgx/config/` 신규 | DataCollector 로부터 수신할 HF 데이터셋 repo_id 목록 등 학습 설정 캐시 관리 |
| `dataset_repos.json` placeholder | HF Hub + rsync 두 방식 모두 지원하는 스키마. 실 값은 05_leftarmVLA 진입 시 채움 |
| `dgx/README.md` 갱신 | pyproject.toml 미존재 + lerobot 설치 방법 주의사항 추가. DataCollector ↔ DGX 인터페이스 섹션 추가. 배포 주의사항 (outputs/, .arm_finetune/ rsync 제외) 명시 |

**변경 이유:**

04_infra_setup TODO-X1 (§5 마이그레이션 계획) 에 따른 dgx/ 구조 정리. 4-노드 분리 아키텍처 (devPC / DataCollector / DGX / 시연장 Orin) 공식화로 DGX 의 학습 전용 책임을 명문화하고, DataCollector 와의 데이터 인터페이스를 위한 `config/` 디렉터리를 신설.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| upstream lerobot 코드 | 변경 없음 (dgx/lerobot/ 미존재 유지) |
| 기존 02 산출물 (setup_train_env / preflight / smoke / save_dummy_checkpoint) | 변경 없음 — 회귀 없음 확인은 TODO-X3 |
| Orin inference path | 영향 없음 |
| DataCollector 인터페이스 | dataset_repos.json placeholder 신설 — 실 운용은 TODO-T1 결정 후 |

**검증:**

- `dgx/tests/README.md` 신규 파일 존재 확인
- `dgx/config/README.md` 신규 파일 존재 확인
- `dgx/config/dataset_repos.json` valid JSON 확인
- `dgx/README.md` 주의사항 섹션 추가 확인
- `dgx/scripts/` 미변경 확인 (02 산출물 회귀 없음)

---

### [2026-05-03] `dgx/scripts/setup_train_env.sh` — lerobot extras hardware,feetech 추가 (07 TODO-D5)

**대상 파일:** `dgx/scripts/setup_train_env.sh`

**변경 내용:**

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| §3 editable install extras | `[smolvla,training]` | `[smolvla,training,hardware,feetech]` |
| §3-c 주석 | "record + hardware + feetech extras 설치" | "torchcodec 별도 인덱스 설치 + dataset 보완 / §3 extras 통합 완료 명시" |

**변경 이유:**

06_dgx_absorbs_datacollector 결정에서 DGX 가 데이터 수집 책임 흡수 시 `setup_train_env.sh` 의 lerobot extras 갱신이 누락되었다. 06 사이클에서는 `§3-c` 를 별도 추가하여 개별 패키지 pip install 방식으로 처리했으나, editable install extras 에 `hardware,feetech` 가 포함되지 않아 07 TODO-D4 preflight check lerobot-find-port 실행 시 pyserial ImportError 가 발생했다 (07 D4 진단).

lerobot upstream `pyproject.toml` extras 정의 (직접 인용):
```
# docs/reference/lerobot/pyproject.toml line 110-114
hardware = [
    "lerobot[pynput-dep]",
    "lerobot[pyserial-dep]",
    "lerobot[deepdiff-dep]",
]
# line 145
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]
```

Option B 원칙 유지: `dgx/pyproject.toml` 신규 생성 X. `dgx/lerobot/` 변경 X. `setup_train_env.sh` 에서만 extras 관리.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| upstream lerobot 코드 | 변경 없음 (dgx/lerobot/ 미존재 유지) |
| setup_train_env.sh 재실행 시 | lerobot[hardware,feetech] (pynput, pyserial, deepdiff, feetech-servo-sdk) 자동 설치 |
| 07 D4 precheck — lerobot-find-port | pyserial ImportError 해소 (영구 fix) |
| §3-c 의 개별 pip install | 중복 설치 — pip no-op 으로 처리됨. 제거는 차기 cleanup 사이클 후보 |

**검증:**

- `bash -n dgx/scripts/setup_train_env.sh` PASS
- extras 키 `hardware`, `feetech` — lerobot upstream `pyproject.toml` 직접 확인 (line 110, 145)

---

### [2026-05-04] `dgx/interactive_cli/flows/precheck.py` — v4l2 메타 device 필터링 + viewer 안내 강화 (07 TODO-D8)

**대상 파일:** `dgx/interactive_cli/flows/precheck.py`

**변경 내용 (Part II — setup_train_env.sh deepdiff 현황 확인):**

lerobot upstream `pyproject.toml` extras 직접 확인:
```
# docs/reference/lerobot/pyproject.toml line 110-114 (D5 인용 동일)
hardware = [
    "lerobot[pynput-dep]",
    "lerobot[pyserial-dep]",
    "lerobot[deepdiff-dep]",        ← deepdiff 포함
]
# line 140
deepdiff-dep = ["deepdiff>=7.0.1,<9.0.0"]
# line 145
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]
```

`setup_train_env.sh` §3 현재 extras: `[smolvla,training,hardware,feetech]` → hardware + feetech 모두 `lerobot[deepdiff-dep]` 포함.
§3-c 에도 `deepdiff>=7.0.1,<9.0.0` 명시 개별 설치 중 (D5 cycle 2 에서 추가된 중복 설치).

**D8 Part II 결론**: `setup_train_env.sh` 변경 불필요.
- `[hardware,feetech]` extras 가 deepdiff-dep 을 transitive 포함 (D5 fix 이미 완료).
- §3-c 의 deepdiff 별도 설치 라인은 중복 (07 BACKLOG #3 — 차기 정리 후보).
- deepdiff 누락이 reported 된 이유: D5 fix 이전 환경에서 venv 미재설치 시 미적용. 재설치 시 해소.

**변경 내용 (Part III — v4l2 메타 device 필터링):**

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| `_get_streamable_video_devices` | 미존재 | 신규 추가 — cv2.VideoCapture read 성공 device 만 반환 |
| `_run_find_cameras_split` baseline | `_get_video_devices()` (전체 glob) | `_get_streamable_video_devices()` (스트림 가능 device 만) |
| `_run_find_cameras_split` baseline_restored | `_get_video_devices()` | `_get_streamable_video_devices()` |
| 분리 후 after 상태 | `_get_video_devices()` | `_get_video_devices()` 유지 (비교 기준 유지) |

레퍼런스:
```
# lerobot/src/lerobot/cameras/opencv/camera_opencv.py line 308, 343-348
camera = cv2.VideoCapture(target)
if camera.isOpened():
    ret, frame = camera.read()  # metadata device 는 ret=False 반환
```

**변경 내용 (Part IV — ssh-file viewer 안내 강화):**

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| ssh-file 모드 안내 | path 출력 + xdg-open 시도 (결과 미보고) | VSCode remote-ssh Explorer 클릭 안내 + code -r 명령 안내 추가 |
| xdg-open 결과 | 실패 시 silent 무시 | poll() 로 성공/실패 명시 보고 |
| X11 fallback 안내 | "ssh -Y 재접속" 1 줄 | libgtk2.0-dev 미설치 원인 후보 추가 |

**변경 이유:**

D8 walkthrough 3 차단 사항 해소:
- (III) wrist 분리 시 video0+video1 둘 다 사라짐 — v4l2 metadata device 가 baseline 에 포함되어 복수 device 사라짐 경고 발생. streamable 필터로 main stream device 만 baseline 에 포함.
- (IV) ssh-file 모드에서 사용자가 영상을 어디서 볼지 불명확. VSCode remote-ssh 사용법 명시.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| upstream lerobot 코드 | 변경 없음 (dgx/lerobot/ 미존재 유지) |
| `_get_video_devices()` | 변경 없음 (backward-compat 보존) |
| `_run_find_cameras_split` | baseline 이 streamable device 만으로 필터링 → metadata device 误検出 해소 |
| `_show_frame` ssh-file | 안내 강화 — 기능 동작 변경 없음 |

**검증:**

- `python3 -m py_compile dgx/interactive_cli/flows/precheck.py` PASS
- `ruff check dgx/interactive_cli/flows/precheck.py` PASS (TODO-D8 완료 후 확인)
