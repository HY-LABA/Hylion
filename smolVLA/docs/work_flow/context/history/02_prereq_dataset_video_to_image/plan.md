# Execution Plan — 02_prereq_dataset_video_to_image

> 작성: 2026-05-15 | planner
> 갱신: 2026-05-16 (재호출 — TODO-1a-fix 완료 + 사용자 PHYS_REQUIRED 결과 수신 + TODO-1b 폐기 + TODO-02·03 활성화)
> spec: `docs/work_flow/specs/02_prereq_dataset_video_to_image.md`

---

## 이전 plan 대비 변경 요약 (2026-05-16)

- **TODO-1a [x] 완료**: cleanup_helper.sh + exp_a_cleanup_attempt3.md + training_log.md 시도 3 양식. code-tester READY_TO_SHIP, prod-test-runner NEEDS_USER_VERIFICATION.
- **TODO-1a-fix [x] 완료**: train_config.yaml `dataset_video_backend: pyav` + run_train.py pyav 인자 추가. 사용자 PHYS_REQUIRED 실험 A 재시도 성공 (학습 진입 + step 진행).
- **사용자 PHYS_REQUIRED 결과 수신**: 학습 진입 정상, 누수 1.07 GB/min (시도 1·2 와 동일), process RSS 안정. 결론: video decode 자체가 leak 원인. backend·workers 가설 분리 완료.
- **TODO-1b [폐기]**: workers RSS 안정으로 실험 B 의미 소멸. 폐기 확정.
- **TODO-02·03 활성화**: 선결 조건 해소. 사용자 결정: "OOM 까지 두고 image 변환 진입". 즉시 dispatch 가능.
- **lerobot 코드 패턴 사전 조사 완료** (planner, Cat A read-only): image dataset 구조·dtype·parquet 패턴 정리 — 아래 §lerobot 패턴 메모 참조.

---

## spec 본문 언급 파일 실존 검증 결과

| 파일·경로 | 상태 | 비고 |
|---|---|---|
| `dgx/finetune/leftarm_v2/config/base_config.yaml` | 실존 확인 | 기존 파일 |
| `dgx/finetune/leftarm_v2/config/train_config.yaml` | 실존 확인 + 갱신됨 | TODO-1a-fix 로 `dataset_video_backend: pyav` 추가됨 |
| `dgx/finetune/leftarm_v2/run_train.py` | 실존 확인 + 갱신됨 | TODO-1a-fix 로 pyav 인자 추가됨 |
| `dgx/docs/finetune/leftarm_v2/training_log.md` | 실존 확인 | 시도 3 entry 포함 |
| `dgx/finetune/leftarm_v2/experiments/` | 실존 확인 | TODO-1a 로 신설됨 |
| `dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh` | 실존 확인 | TODO-1a 산출 |
| `dgx/finetune/leftarm_v2/experiments/exp_a_cleanup_attempt3.md` | 실존 확인 | TODO-1a 산출 |
| `dgx/finetune/leftarm_v2/convert_to_image.py` | (신규) | TODO-02 작성 대상 |
| `docs/work_flow/context/research/m1.5_video_decode_oom.md` | 실존 확인 | TODO-01 산출 완료 |

---

## lerobot 패턴 메모 (Cat A read-only 조사 결과 — task-executor 참조용)

### image dtype

`docs/reference/lerobot/src/lerobot/datasets/dataset_metadata.py` L311:
```python
def image_keys(self) -> list[str]:
    return [key for key, ft in self.features.items() if ft["dtype"] == "image"]
```

info.json 의 features dict 에서 image 키의 `"dtype"` 값은 정확히 `"image"` (소문자). `"video"` → `"image"` 로 변경 시 이 값 사용.

### image 파일 경로 패턴

`docs/reference/lerobot/src/lerobot/datasets/utils.py` L90:
```python
DEFAULT_IMAGE_PATH = "images/{image_key}/episode-{episode_index:06d}/frame-{frame_index:06d}.png"
```

즉 image dataset 의 frame 파일 경로: `images/<obs_key>/episode-000000/frame-000000.png`

### parquet 내 image 컬럼 저장 방식

`dataset_writer.py` L210: image dtype 프레임 → parquet 컬럼에 `str(img_path)` (파일 경로 문자열) 저장.
`feature_utils.py` L51: HuggingFace feature 레벨에서는 `datasets.Image()` 로 매핑.
`io_utils.py` L98-115: `embed_images()` — Arrow 직렬화 시 image bytes 를 Arrow table 에 embed.

**결론**: image dataset parquet 은 image 컬럼에 *PIL Image 또는 path/bytes 구조체* 저장. lerobot 이 자체 `embed_images()` 를 통해 처리. task-executor 의 convert_to_image.py 는 아래 중 한 방법 선택:

1. **방법 A (lerobot API 활용)**: `dataset_tools.py` 의 `convert_image_to_video_dataset` 의 *역방향* — lerobot 의 `LeRobotDataset.create()` + `DatasetWriter` 로 frame-by-frame 기록. lerobot 이 parquet/images/ 구조를 자동 처리. 가장 안전하나 구현 복잡.
2. **방법 B (직접 추출 + 메타 조작)**: pyav 로 mp4 frame 추출 → `images/<key>/episode-XXXXXX/frame-XXXXXX.png` 저장 → parquet 의 video 참조 컬럼 제거 + image path 컬럼 추가 → info.json `dtype` `"video"` → `"image"` 변경. 구현 단순하나 lerobot 내부 포맷 정합 책임이 task-executor 에.

**권장**: task-executor 는 방법 B 를 기반으로 진행. 단 parquet image 컬럼은 `str(img_path)` 가 아닌 HuggingFace `datasets.Image()` 포맷 (`PIL.Image` 객체 또는 bytes dict) 으로 저장해야 `LeRobotDataset` 로드 시 인식됨. `to_parquet_with_hf_images()` 또는 `embed_images()` 를 참조해 올바른 직렬화 적용.

핵심 파일 참조:
- `docs/reference/lerobot/src/lerobot/datasets/dataset_tools.py` L1648 `convert_image_to_video_dataset` — 역방향 패턴
- `docs/reference/lerobot/src/lerobot/datasets/io_utils.py` L98 `embed_images`
- `docs/reference/lerobot/src/lerobot/datasets/utils.py` L90 `DEFAULT_IMAGE_PATH`
- `docs/reference/lerobot/src/lerobot/datasets/feature_utils.py` L50 image dtype → `datasets.Image()` 매핑

---

## DAG

### Group 1 — 완료

- **TODO-01** [x] researcher 보고서 작성 완료
  - 산출: `docs/work_flow/context/research/m1.5_video_decode_oom.md`
  - verdict: `NEEDS_INVESTIGATION`
  - 상태: 자동화 완료 (2026-05-15).

- **TODO-1a** [x] 실험 A 절차 문서 + cleanup_helper.sh 완료
  - 산출: `dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh`, `exp_a_cleanup_attempt3.md`
  - code-tester: READY_TO_SHIP, prod-test-runner: NEEDS_USER_VERIFICATION
  - 사용자 PHYS_REQUIRED 완료 (2026-05-16): 학습 진입 성공, OOM 누수 1.07 GB/min 확인

- **TODO-1a-fix** [x] video_backend=pyav 강제 적용 완료
  - 산출: `dgx/finetune/leftarm_v2/config/train_config.yaml` L37 갱신, `run_train.py` L89·L121 갱신
  - code-tester: READY_TO_SHIP, prod-test-runner: NEEDS_USER_VERIFICATION (자동 검증 7/7)
  - 사용자 PHYS_REQUIRED 완료 (2026-05-16): 학습 진입 + step 진행 정상. 누수 동일 (1.07 GB/min).

---

### Group 2-EXP-B — 폐기

- **TODO-1b** [폐기] — 실험 A 데이터로 workers RSS 안정 확인 → workers 가설 분리 완료, 실험 B 의미 소멸 (2026-05-16)

---

### Group 2-A — 활성 (image 변환)

- **TODO-02**: video → image 변환 스크립트 작성 + DGX 실행
  - 담당: task-executor → code-tester → prod-test-runner
  - task-executor 산출 경로 (Write 필수 — ORCHESTRATOR_GAP 재발 차단):
    - Write 필수: `dgx/finetune/leftarm_v2/convert_to_image.py` (신규)
    - DGX 실행 결과 (prod-test-runner 또는 사용자): `~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image/` (DGX 측 신규 디렉터리 — repo 외)
  - lerobot 참조 (Cat A read-only):
    - `docs/reference/lerobot/src/lerobot/datasets/dataset_tools.py` L1648 `convert_image_to_video_dataset` — *역방향 패턴* 참조
    - `docs/reference/lerobot/src/lerobot/datasets/utils.py` L90 `DEFAULT_IMAGE_PATH` — image 파일 경로 규칙
    - `docs/reference/lerobot/src/lerobot/datasets/io_utils.py` L98 `embed_images` — parquet 직렬화
    - `docs/reference/lerobot/src/lerobot/datasets/feature_utils.py` L50 — image dtype HuggingFace 매핑
  - 환경 레벨:
    - 스크립트 작성: AUTO_LOCAL (devPC)
    - DGX 변환 실행: SSH_AUTO 가능 (단 110ep × 2cam × 평균 ~500 frame ≈ 100k+ frame 추출 → 1-3시간 소요 예상). prod-test-runner 가 시간 초과 가능성 판단 후 사용자 위임 결정.
  - DOD (spec §TODO-02):
    - (a) `convert_to_image.py` 신규 — mp4 frame 추출, parquet 재작성, meta/info.json `"video"` → `"image"` 변경
    - (b) DGX 실행 — 원본 `leftarm_v2` 무손상, 새 `leftarm_v2_image` 생성 (110ep 전체)
    - (c) 새 dataset 디스크 사용량 측정·기록
  - 검증: `LeRobotDataset(repo_id=..., root=...)` 로드 성공 + `image_keys` 인식 + episode/frame count 원본 일치

---

### Group 3 — 활성 (train_config 갱신 + 시도 학습) — TODO-02 완료 후

- **TODO-03**: train_config 갱신 + 시도 3 학습 진입
  - 담당: task-executor (config 갱신) → code-tester (dry-run 검증) → 사용자 (학습 진입 PHYS_REQUIRED)
  - task-executor 산출 경로 (Write 필수):
    - `dgx/finetune/leftarm_v2/config/base_config.yaml` 갱신 (dataset repo_id/root → `leftarm_v2_image`)
    - `dgx/finetune/leftarm_v2/config/train_config.yaml` 갱신 (image dataset 전용 — `dataset.video_backend` 제거 또는 무시 설정)
    - `run_train.py` 검토 후 변경 필요 시 갱신 (image dataset 인식 자동이라 무변경 가능성 높음)
  - 환경 레벨:
    - config 작성: AUTO_LOCAL
    - DGX dry-run: SSH_AUTO
    - 시도 3 학습 진입: PHYS_REQUIRED (사용자 직접)
  - **변수 분리 핵심**: 시도 1·2·3 와 학습 인자 (`steps=20000`, `batch=16`, LoRA r=16 등) 동일 유지. `video → image` 변경 *만* 적용.
  - DOD (spec §TODO-03):
    - (a) config 갱신 — dataset → `leftarm_v2_image` 지정
    - (b) `run_train.py` 검토 — image 인식 자동 여부 확인 (변경 필요 시만)
    - (c) dry-run 통과 — 새 dataset 인식 오류 없음
    - (d) 시도 3 학습 진입 + 첫 1000 step ckpt 도달 + OOM 없음 + wandb run URL 기록

---

## 확신 가정 (병렬 진행 OK)

- **가정 1**: `dgx/finetune/leftarm_v2/experiments/` 는 TODO-1a 로 이미 신설됨. Category C 재검토 불요.
- **가정 2**: `cleanup_helper.sh` 내 `pkill -9` 명령은 Category D 미해당. 스크립트 파일 자체 작성은 Bash 직접 실행 X — 파일 Write 이므로 deny 규칙 미적용.
- **가정 3**: `dgx/finetune/leftarm_v2/config/train_config.yaml` 은 TODO-1a-fix 로 갱신 완료 (`dataset_video_backend: pyav`). TODO-03 에서 image dataset 전용으로 재갱신 (dataset 경로 변경, video_backend 제거 또는 유지).
- **가정 4**: BACKLOG drift 5건 (#2~#6) 은 본 사이클 처리 외. BACKLOG #1 (`deploy_orin.sh`) — Category C 상태 유지.
- **가정 5**: `docs/reference/lerobot/` 하위는 Category A read-only. task-executor 참조만 가능, 수정 X.
- **가정 6**: 원본 `leftarm_v2` dataset (`~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/`) 보존 필수. convert_to_image.py 는 *사본 작업* — 원본 경로 접근 read-only.
- **가정 7**: DGX SSH 접속 — prod-test-runner 자율 가능. 학습 실행 (TODO-03 (d)) — PHYS_REQUIRED.
- **가정 8 (확인됨)**: TODO-1a 산출 문서 사용자 독자 수행 가능 — 실험 A 사용자 직접 수행 성공으로 confirm.
- **가정 9 (신규 — 실험 A 데이터 근거)**: video decode 자체가 leak 원인 확정. backend (torchcodec/pyav) 무관, workers RSS 안정으로 process 외부 leak 확인. image 변환이 유일한 근본 해법으로 확정. researcher §5 옵션 3 채택 confirm.
- **가정 10 (신규)**: `dgx/finetune/leftarm_v2/convert_to_image.py` 신설 — `dgx/` 내부 신규 파일이므로 Category C 미해당. task-executor 자율 작성 가능.
- **가정 11 (신규)**: `leftarm_v2_image/` 신규 디렉터리 — DGX 측 `~/smolvla/.hf_cache/lerobot/BaboGaeguri/` 내부 (repo 외부, 사용자 hf_cache). Category C 미해당. prod-test-runner 가 DGX 에서 스크립트 실행 시 자율 생성 가능.
- **가정 12 (신규)**: lerobot image dataset 의 `info.json` features 내 image 키의 `"dtype"` 값은 정확히 `"image"` (소문자). `dataset_metadata.py` L311 직접 확인.
- **가정 13 (신규)**: lerobot image dataset 의 frame 파일 경로 규칙은 `DEFAULT_IMAGE_PATH = "images/{image_key}/episode-{episode_index:06d}/frame-{frame_index:06d}.png"` (`utils.py` L90 확인). task-executor 가 convert_to_image.py 작성 시 이 경로 패턴 준수.

---

## 확인 필요 가정 (awaits_user)

| TODO | 질문 | 영향 | 분류 |
|---|---|---|---|
| TODO-02 DGX 변환 실행 | 110ep × 2cam × ~500 frame ≈ 100k+ 프레임. 소요 시간 1-3시간 예상. SSH_AUTO 시도 시 timeout 가능. prod-test-runner 가 실행 시작 후 timeout 판단 → 사용자 위임 결정 자율. | Group 3 (TODO-03) 진입 시점 결정 | `awaits_user` (SSH_AUTO 시도 후 판단) |
| TODO-03 시도 학습 진입 (d) | 사용자 직접 DGX 에서 학습 실행 + 1000 step + OOM 없음 + wandb URL 기록 후 `/verify-result` | Phase 3 wrap 진입 여부 결정 | `awaits_user` (PHYS_REQUIRED) |

---

## Phase 3 검증 큐 후보

| TODO | 환경 레벨 | 검증 방식 | 비고 |
|---|---|---|---|
| TODO-01 (researcher 보고서) | `AUTO_LOCAL` | 완료 — 보고서 존재, §3~§5 충족. | Phase 3 검증 불요 |
| TODO-1a (cleanup_helper.sh + 절차 문서) | `AUTO_LOCAL` | 완료 — code-tester READY_TO_SHIP. | Phase 3 검증 불요 |
| TODO-1a (DGX dry-run) | `SSH_AUTO` | 완료 — prod-test-runner SSH 5/5. | Phase 3 검증 불요 |
| TODO-1a (실험 A 학습) | `PHYS_REQUIRED` | 완료 — 사용자 실행, 누수 1.07 GB/min 확인. | Phase 3 검증 불요 |
| TODO-1a-fix (자동 검증) | `AUTO_LOCAL` + `SSH_AUTO` | 완료 — code-tester READY_TO_SHIP, prod-test-runner 자동 검증 7/7. | Phase 3 검증 불요 |
| TODO-1a-fix (실험 A 재시도) | `PHYS_REQUIRED` | 완료 — 사용자 실행 성공, 변수 분리 결론 도출. | Phase 3 검증 불요 |
| TODO-02 (스크립트 문법 + smoke) | `AUTO_LOCAL` | code-tester: `python -m py_compile convert_to_image.py` + lerobot import smoke. devPC 자율. | 활성 |
| TODO-02 (DGX 변환 실행 + dataset 검증) | `SSH_AUTO` | prod-test-runner: DGX SSH — `leftarm_v2_image/` 존재 + `LeRobotDataset` 로드 smoke (`python -c "from lerobot.datasets.lerobot_dataset import LeRobotDataset; ds = LeRobotDataset(repo_id='BaboGaeguri/leftarm_v2_image', root=...); print(ds.meta.image_keys)"`) + episode/frame count 원본 일치 확인. 변환 시간 1-3h 예상 → timeout 시 사용자 위임. | 활성 (시간 소요 주의) |
| TODO-03 (config 갱신 + dry-run) | `AUTO_LOCAL` + `SSH_AUTO` | code-tester: YAML 문법 + dataset 경로 변경 확인. prod-test-runner: DGX dry-run (`python run_train.py train --pass 2a --dry-run`) — 새 dataset 인식 오류 없음 확인. | 활성 |
| TODO-03 (시도 3 학습 진입) | `PHYS_REQUIRED` | 사용자 직접 DGX 에서 학습 실행. 첫 1000 step ckpt 도달 + OOM 없음 + wandb peak 기록. `/verify-result` 로 결과 보고. | 활성 — 최종 사용자 검증 |

---

## researcher ORCHESTRATOR_GAP 재발 차단 지침

ANOMALIES #1 (2026-05-15): researcher 산출 경로 Write 누락.

다음 dispatch 에서 task-executor 에게 산출 경로를 다음 형식으로 명시:

```
산출 파일:
- Write 필수: `dgx/finetune/leftarm_v2/convert_to_image.py`
텍스트 반환만으로는 산출 미완성 — 반드시 Write tool 로 파일 저장 완료 후 done 보고.
```

orchestrator 는 task-executor 완료 보고 직후 해당 파일 존재 여부를 `Bash(ls)` 로 즉시 확인. 미존재 시 재dispatch.

---

## 주요 흐름 요약

```
[Group 1 — 완료]
  TODO-01: researcher 보고서
    → verdict: NEEDS_INVESTIGATION
  TODO-1a: cleanup_helper.sh + 절차 문서
    → code-tester READY_TO_SHIP
    → prod-test-runner NEEDS_USER_VERIFICATION
    → [사용자 PHYS_REQUIRED 완료] 실험 A 결과: 누수 1.07 GB/min, backend·workers 변수 분리
  TODO-1a-fix: pyav 강제
    → code-tester READY_TO_SHIP
    → prod-test-runner NEEDS_USER_VERIFICATION (자동 7/7)
    → [사용자 PHYS_REQUIRED 완료] 학습 진입 정상, 누수 동일 → video decode 자체 원인 확정

[Group 2-EXP-B — 폐기]
  TODO-1b: 폐기 (workers RSS 안정으로 실험 의미 소멸)

[Group 2-A — 즉시 진입]
  TODO-02: task-executor
    → convert_to_image.py 작성 (Write 필수: dgx/finetune/leftarm_v2/convert_to_image.py)
    → code-tester (AUTO_LOCAL: py_compile + smoke)
    → prod-test-runner (SSH_AUTO: DGX 변환 실행 + leftarm_v2_image 검증)
    → [awaits_user 가능] 변환 1-3h 시간 초과 시 사용자 위임

[Group 3 — TODO-02 완료 후]
  TODO-03: task-executor
    → config/base_config.yaml + train_config.yaml 갱신 (Write 필수)
    → code-tester (AUTO_LOCAL: YAML 문법)
    → prod-test-runner (SSH_AUTO: dry-run)
    → [awaits_user] PHYS_REQUIRED: 사용자 시도 3 학습 실행 + 1000 step + OOM 없음 확인

[Phase 3 — 사용자 검증]
  /verify-result: 첫 1000 step ckpt 도달 + OOM 없음 + wandb URL
  통과 → /wrap-spec
  실패 → planner 재호출 → 추가 todo
```
