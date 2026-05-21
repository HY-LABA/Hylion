# prof_computer — DGX 보조 학습 노드 (WSL2 + RTX 3090)

> [prof_train_setting.md](../docs/storage/prof_train_setting.md) §1 옵션 #1 "로컬 GPU PC" 의 구체 구현체.
> 시연장 외 (개발실·실험) 학습 수행. DGX 의 aarch64 한계 (torchcodec 부재 → pyav fallback leak) 우회를 위한 일반 x86 학습 노드.
> 등록: 2026-05-16 · **M1.5 중간점검 학습 완주: 2026-05-17** (leftarm_v2 100ep subset, 75000 step)
> 실측 사양: [02_hardware.md §6](../docs/storage/02_hardware.md) · 소프트웨어: [03_software.md §7](../docs/storage/03_software.md)
>
> **위치**: M1 (**400ep** 수집 중, 110ep 도달 — 2026-05-18 목표 200→400 조정) → **M1.5 (완료 — prof_computer 이관, video dataset 그대로 학습 성공)** → M2 (400ep 완성 후 본 학습, 미시작) → M3 (Orin 추론).

## 1) 노드 정체성

| 항목 | 값 |
|---|---|
| 호스트 | `DESKTOP-G8LO9C5` (Windows 10 + WSL2 Ubuntu 22.04) |
| GPU | RTX 3090 **24GB VRAM** (분리 — DGX UMA 와 다름) |
| 학습 distro | `Ubuntu-22.04` (WSL2), 사용자 `laba` |
| Python | **`3.12.x` (deadsnakes PPA)** + venv (`.venv_arm_finetune`) — lerobot 0.5.2 `requires-python>=3.12` 충족용. 시스템 3.10.12 와 병존. |
| 데이터 | HF Hub (`BaboGaeguri/leftarm_v2` 등) — DGX 와 공유 |
| 작업 영역 | `smolVLA/prof_computer/` (본 폴더) |

## 2) DGX 와의 분담

- **공유**: 데이터셋 (HF Hub) + lerobot upstream (`docs/reference/lerobot/`). DGX 의 *수집 config* (`dgx/finetune/leftarm_v2/{base,record}_config.yaml`) 는 *DGX 노드 한정* — 학습 config 는 prof_computer 측 (`prof_computer/finetune/leftarm_v2/config/`) 자체 보유 (2026-05-18 DGX 학습 잠정 중단 후 분리).
- **분리**: venv 위치, 학습 산출물 (`~/prof_computer_runs/` vs DGX `~/smolvla/dgx/outputs/`), wandb run name (`_pc_` 접두로 구분)

## 3) DGX vs prof_computer — 메모리 모델 차이 (운영 핵심)

| 차원 | DGX (UMA 128GB) | prof_computer (분리) |
|---|---|---|
| GPU 메모리 | UMA 공유 (VRAM 별도 없음) | **24GB VRAM (분리)** |
| system RAM | UMA 공유 | 64GB (WSL 48GB 할당) |
| swap | 0 | 16GB (`.wslconfig`) |
| OOM 위협 1순위 | system 전체 OOM (`CONSTRAINT_NONE`) | **VRAM OOM** |
| OOM 위협 2순위 | UMA 헤드룸 부족 | system RAM 누수 (시도 2 가설 잔존) |

→ DGX 의 시도 1·2 OOM (`training_log.md`) 은 UMA 특수 사정. prof_computer 에서는 **VRAM 24GB 가 새 제약** + system RAM 누수 가설 그대로.

## 4) 채택한 사전 조치 (training_log §시도2 "시도 3 후보" 선제 반영)

| 조치 | 근거 |
|---|---|
| `video_backend=torchcodec` | 시도 2 의 시간 비례 누수 = pyav-libsvtav1 decoder leak 가설 → backend 교체로 회피 |
| `.wslconfig memory=48GB` + swap 16GB | 누수 발생 시 시간 벌이 |
| smoke test 우선 (steps=100) | 본 학습 20K step 전에 VRAM peak + 누수율 실측 |

## 5) 폴더 구조 (planned)

```
prof_computer/
├── README.md                       # 본 파일
├── scripts/
│   ├── setup_env.sh                # WSL apt + venv + lerobot/torchcodec 설치
│   ├── env_check.sh                # 학습 전 환경 검증
│   └── run_train.sh                # finetune/leftarm_v2/run_train.py 호출 래퍼 (선택)
├── finetune/
│   └── leftarm_v2/
│       ├── README.md               # 학습 entry 소개 + 분기 사용법
│       ├── config/                 # 학습 config (DGX 분리 후 자체 보유)
│       ├── run_train.py            # 001 분기 원본 학습 entry
│       └── run_train_camera_empty.py  # camera_empty 검증 분기 entry
└── docs/
    ├── model_config.md             # 학습 방법 매트릭스·hyperparameter (leftarm_v2/v3+ 공통)
    └── leftarm_v2/                 # leftarm_v2 사이클 한정 자료 (학습 측)
        ├── learning_log1.md        # PC 학습 시도 기록 (M1.5~003 아카이브, 2026-05-21 freeze)
        ├── learning_log2.md        # PC 학습 시도 기록 (현행 — 004+ 사이클)
        ├── research_empty_cameras_2026-05-18.md   # researcher 보고서 (empty_cameras 가설 검증)
        ├── lerobot_smolvla_training_best_practice.md  # researcher 보고서 (학습 모범 사례)
        └── after_run_checklist.md  # 학습 직후 체크리스트

# Orin 추론 평가는 별도 — smolVLA/orin/docs/leftarm_v2/{a2,base,camera_empty}_eval_*.md
# 노드 책임 분리: 학습 자료 = prof_computer / 추론 평가 = orin (2026-05-19 정리)
```

> ⚠️ **upstream 옵션 B 일관**: prof_computer 도 `docs/reference/lerobot/` editable install 을 그대로 사용 — DGX 와 같은 정책. lerobot 코드 분기 없음.

## 6) 사용 시점 트리거

- DGX 가동·이동 불가
- 새 hyperparameter 후보를 DGX 본 학습 전에 빠르게 실험
- 동일 dataset 으로 DGX 와 결과 비교

## 7) 명명 3-계층 + 시간 라벨 (cold start 시 첫 1독)

본 프로젝트의 학습 관련 명명은 *3개 영구 계층* + *별도 시간 라벨* 로 분리된다. 새로 합류하는 사람·AI 가 헷갈리지 않도록 *반드시 본 § 먼저 읽고* 다른 문서 진입.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ⏱ 시간 라벨 (era + 마일스톤)  ← 영구 계층 외부, 분기 식별에 사용 금지         │
│   leftarm_v2 era · M1 / M1.5 / M2 / M3 / M4                                │
│   "현 era 동안의 *작업 일정* 분류"                                            │
│   정본: realplaying.md (해당 era 동안만 살아있음 — era 종료 시 의미 휘발)       │
│   사용처: era 진행 중의 *작업 순서 추적*. 분기 식별·결정 근거에 등장 금지.       │
└────────────────────────────────────────────────────────────────────────────┘
                                  ⇣ 외부 메타 (분기 entry 의 *시기 맥락* 만 표시)
┌────────────────────────────────────────────────────────────────────────────┐
│ 계층 1 — 학습 방법  (A1 / A2 / B1 / B2 / C1 / C2)                             │
│   "VLM·expert 를 어떻게 학습? (LoRA / Full FT / frozen 매트릭스)"               │
│   영구 분류 — 모델 구조 기반. VLA 분야가 살아있는 한 의미 안 변함.               │
│   정본: [docs/model_config.md §2 매트릭스](docs/model_config.md)                │
└─────────────────────────────┬──────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 계층 2 — hyperparameter 인자                                                 │
│   dataset 크기·empty_cameras·scheduler·bf16·batch·lr·steps·wrist_rot ...     │
│   영구 분류 — lerobot/SmolVLA 표준 인자.                                       │
│   정본: [docs/model_config.md §3 권장값 + 다음 시도 후보](docs/model_config.md)  │
└─────────────────────────────┬──────────────────────────────────────────────┘
                              │ 학습 방법 + 인자 묶음 = 1 분기 인스턴스
                              ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 계층 3 — 분기 인스턴스  (001 / 002 / 003 / 004 / ...)                          │
│   "이 방법 + 이 인자로 *학습된* 모델 ckpt = 1 분기"                              │
│   자기서술적 — 이름에 *방법 + 핵심 인자* 박힘 (예: 003_a2_310ep_empty1_...).     │
│   영구 분류 — era 와 무관, 이름만으로 정체 추론 가능.                            │
│   정본: finetune/leftarm_v2/branches/<NNN>_<방법>_<인자>/                       │
│   실행 기록: docs/leftarm_v2/learning_log1.md (아카이브) /                      │
│             docs/leftarm_v2/learning_log2.md (현행)                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 7-1) 시간 라벨의 *영구 계층 분리* 원칙

**왜 마일스톤이 *영구 계층 외부* 인가**:

- 시간이 지나면 마일스톤은 *휘발성* — `leftarm_v3 era` 의 "M1" 과 본 era 의 "M1" 은 같은 이름이지만 *완전 다른 정의*. 마일스톤 이름 단독으로는 *어느 era 의 M1 인지* 모름.
- *분기 인스턴스* 는 *영구 인덱스* (001/002/...) + *자기서술적 토큰* — `001_a2_100ep` 가 무엇인지 *이름만으로* 정체 추론 가능. era 와 무관.
- 따라서 분기 식별·결정 근거·실행 로그 어디에도 *마일스톤 이름이 등장하지 않아야 함*. 시간 라벨이 필요한 영역은 *분기 entry 의 메타 박스에 1줄로* 보존 (예: `"본 분기는 leftarm_v2 era · M1.5 마일스톤 시기에 진행"`).

### 7-2) 명명 룰 준수 — 분기 식별 표현

| 영역 | 금지 (마일스톤 직접 인용) | 권장 (자기서술적) |
|---|---|---|
| 분기 vs 분기 비교 | "vs 001 (M1.5 baseline)" | "vs 001 (A2 baseline, 100ep)" |
| 분기 결정 근거 | "M1.5 wandb 분석" | "001 wandb 분석" |
| hp 인용 | "M1.5 동일" | "001 동일" 또는 "(앞 분기) 동일" |
| backlog 메모 | "M1.5 후반 정체" | "001 후반 정체" |

→ **분기 식별엔 *분기 인덱스 (001~) + 방법 (a2 등) + 인자* 만 사용**. 마일스톤 이름 (M1.5 등) 은 *시기 맥락 메타 박스* 에만.

### 7-3) 계층 간 *우연한 1대1 매핑* 주의

| 우연 매핑 | 진실 |
|---|---|
| "M1.5 = 001 분기" | 우연 — M1.5 마일스톤의 학습이 *마침* 001 분기로 인스턴스화됐을 뿐. M1.5 가 *여러 분기* 를 거쳤다면 1대N 매핑이었을 것. *시간 라벨* ↔ *분기 인스턴스* 의 우연한 일치. |
| "A2 = 003 분기" | 우연 — 003 분기가 *A2 방법을 채택해 인스턴스화* 됐을 뿐. A2 는 *영구 카탈로그 카드*, 003 은 *일회성 분기 번호*. **상위 = A2**, **하위 = 003**. |
| "M2 = 003" | 우연 — M2 마일스톤의 학습이 *003 분기* 로 완수됐을 뿐. 다음 era 의 M2 는 다른 분기일 것. |

→ *각 계층은 독립된 분류축*. 하위가 상위를 결정하지 않고, 상위가 하위를 *복수 인스턴스* 로 가질 수 있음.

### 7-4) 분기명 토큰 룰 (계층 3 명명 규약)

분기명 형식: `<NNN>_<방법>_<핵심 인자들>`

| 토큰 | 의미 | 예시 |
|---|---|---|
| `NNN` | 분기 인덱스 (3자리 zero-pad, 0번부터 시작 가능) | `001`, `002`, `003` |
| `<방법>` | 계층 1 매트릭스 cell (소문자) | `a2`, `c1` |
| `<핵심 인자들>` | 변경된 hp 인자들을 짧은 토큰으로 나열 (snake_case) | `100ep`, `310ep`, `empty1`, `sched_sync`, `bf16`, `b6` |

**토큰 표기 규약**:
- *기본값과 다른 인자만* 토큰화. 기본값 ([docs/model_config.md §3 권장값](docs/model_config.md)) 은 생략. 예: `b4` 가 기본값이면 `b4` 토큰 생략.
- *boolean 인자* 는 변경 시 `<인자명><값>` 으로 표기 (예: `empty1` = `empty_cameras=1`). 기본값 (예: `empty_cameras=0`) 인 분기는 토큰 생략.
- *수치 인자* 는 `<인자명약자><값>` (예: `b6` = `batch=6`, `310ep` = dataset 310ep).
- *기능 변경* 은 *짧은 이름* (예: `sched_sync` = scheduler_decay_steps 동기화, `bf16` = mixed precision bf16).

**run prefix 룰** (학습 실행 시):
- 형식: `leftarm_v2_<분기 후반부 식별자>_<pass>_<ts>`
- *분기 후반부 식별자* = 분기명에서 `<NNN>_<방법>_` 를 뗀 *핵심 인자들* (또는 별명) — wandb run 목록에서 분기 추적 용이.
- 예: `001` 의 run prefix = `leftarm_v2_2a_pc_<ts>` (별명 `2a` 사용 — *legacy*), `003` = `leftarm_v2_003_<pass>_<ts>` (분기 인덱스 직접 사용 — *현행 권장*).

**별명·legacy 명명 정책**:
- 003 사이클 이전 분기 (001, 002) 는 *별명 우선* 명명 흔적 잔존 (001 = "M1.5 baseline", 002 = "camera_empty"). *별명* 과 *분기명* 은 1대1 대응이지만 학습 로그·run prefix·HF Hub repo 명에 *섞여 사용* 됨 → 검색 시 *3종 토큰 cross-ref* 필요.
- **004+ 이후 권장**: 별명 사용 *지양*, *분기 인덱스 (NNN) + 핵심 인자 토큰* 만 사용. learning_log entry 제목·run prefix·HF Hub repo 모두 동일 토큰.

### 7-5) "단일 변수 변경" 원칙의 *현 상태*

이전 finetune/leftarm_v2/README 의 *분기 = 단일 변수 변경* 원칙은 *003 사이클에서 5변수 묶음 변경으로 사실상 폐기*. **현 정책**: *단일 변수 분기 + 묶음 분기 모두 허용*. 단:

- *단일 변수 분기* — 결과 해석 깔끔 (어느 변수가 효과인지 즉시 분리)
- *묶음 분기* — 결과 도약 시 *dominant 변수 미분리* 위험 인지 + ablation 사이클 별도 시도 권장

분기 명명 토큰은 *변경된 모든 변수* 를 다 박는 게 룰 (단일/묶음 무관).

---

## 8) 진행 기록·결정 흐름은 어디로?

본 README 는 **노드 영구 정체성 + 명명 컨벤션** 만 다룬다. *시기성 정보* (진행 상황·학습 entry·다음 사이클 결정) 는 별도 문서에 *역할 분리*:

| 정보 종류 | 정본 |
|---|---|
| era 마일스톤 진행·종료 조건·다음 사이클 | [`../realplaying.md`](../realplaying.md) (현 era 동안만 살아있음) |
| 분기별 학습 실행 기록 (smoke/full, 메트릭, 결과) | [`docs/leftarm_v2/learning_log1.md`](docs/leftarm_v2/learning_log1.md) (아카이브) · [`learning_log2.md`](docs/leftarm_v2/learning_log2.md) (현행) |
| 학습 방법 매트릭스·권장 hp·다음 시도 후보 | [`docs/model_config.md`](docs/model_config.md) (영구 카탈로그) |
| 추론 평가 결과 | `../orin/docs/leftarm_v2/*_eval_*.md` |
