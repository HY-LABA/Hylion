# 02. orin/pyproject.toml vs upstream 차이 기록

> 목적: `lerobot/pyproject.toml` (upstream submodule) 대비 `orin/pyproject.toml`의 변경 사항을 누적 기록한다.
> upstream 기준 commit: `ba27aab79c731a6b503b2dbdd4c601e78e285048` (v0.5.1-42, 2026-04-22 동기화)

---

## 현재 차이 요약

### 1. `requires-python`

| | upstream | orin |
|---|---|---|
| 값 | `>=3.12` | `>=3.10` |
| 이유 | Python 3.12 공식 지원 | JetPack 6.2.2 → jp6/cu126 wheel이 cp310만 제공 |

### 2. `torch` / `torchvision` — 의존성에서 제거

| | upstream | orin |
|---|---|---|
| torch | `>=2.7,<2.11.0` | **제거** |
| torchvision | `>=0.22.0,<0.26.0` | **제거** |
| 관리 위치 | pyproject.toml | `orin/scripts/setup_env.sh` |

**제거 이유:**

`pyproject.toml`에 torch를 명시하면 `pip install -e .` 실행 시 pip가 aarch64에서 접근 가능한 PyPI CPU-only wheel(예: torch 2.6.0)로 덮어쓴다.  
jp6/cu126 CUDA wheel은 `--extra-index-url`로만 접근 가능하므로 `setup_env.sh`에서 lerobot 설치 완료 후 `--force-reinstall --no-deps`로 별도 설치한다.

관련 변경 이력: [2026-04-23] — 아래 변경 이력 참조.

### 3. 패키지 메타데이터 — 제거

upstream에 있고 orin에 없는 항목:

| 항목 | 비고 |
|---|---|
| `[project.urls]` | HuggingFace/GitHub 링크 |
| `license`, `authors`, `classifiers`, `keywords` | 오픈소스 배포용 메타데이터 |
| `dynamic = ["readme"]` | PyPI 배포용 |

Orin 패키지는 내부 배포용이므로 불필요.

### 4. Optional extras — 대폭 축소

upstream은 수십 개의 extra를 지원하며 내부적으로 `lerobot[sub-extra]` 형태의 중첩 의존성을 사용한다.  
orin은 실행에 필요한 3개 extra만 유지하며, 중첩 참조 없이 패키지를 직접 나열한다.

**유지된 extras:**

| extra | upstream 방식 | orin 방식 |
|---|---|---|
| `smolvla` | `lerobot[transformers-dep]` (간접) | `transformers==5.3.0` (직접) |
| `hardware` | `lerobot[pynput-dep]`, `lerobot[pyserial-dep]`, `lerobot[deepdiff-dep]` | `pynput`, `pyserial`, `deepdiff` (직접) |
| `feetech` | `feetech-servo-sdk`, `lerobot[pyserial-dep]`, `lerobot[deepdiff-dep]` | 직접 나열 |
| `zmq` | 동일 (`pyzmq`) | — |

**제거된 extras (upstream에만 존재):**

`dataset`, `training`, `viz`, `core_scripts`, `evaluation`, `all`,  
`dynamixel`, `damiao`, `robstride`, `gamepad`, `hopejr`, `lekiwi`, `unitree_g1`, `reachy2`, `kinematics`, `intelrealsense`, `phone`,  
`diffusion`, `wallx`, `pi`, `multi_task_dit`, `groot`, `sarm`, `xvla`, `hilserl`,  
`aloha`, `pusht`, `libero`, `metaworld`,  
`dev`, `notebook`, `test`, `video_benchmark`, `peft`, `async`

### 5. `[project.scripts]` — 04_infra_setup TODO-O2 시점 정리 (2026-04-30)

upstream 14개 중 04 의 4-노드 분리 후 Orin 책임 (추론 + 데이터 수집 + 환경 점검) 에 맞는 9개만 등록. 학습/평가 entrypoint 2개 제거.

| 스크립트 | orin 포함 여부 |
|---|---|
| `lerobot-calibrate` | ✅ |
| `lerobot-find-cameras` | ✅ |
| `lerobot-find-port` | ✅ |
| `lerobot-find-joint-limits` | ✅ |
| `lerobot-record` | ✅ |
| `lerobot-replay` | ✅ |
| `lerobot-setup-motors` | ✅ |
| `lerobot-teleoperate` | ✅ |
| `lerobot-eval` | ❌ (04 TODO-O2 제거: Orin 평가 안 함, hil_inference.py 또는 DGX 가 대체) |
| `lerobot-train` | ❌ (04 TODO-O2 제거: Orin 학습 안 함, DGX 책임) |
| `lerobot-info` | ✅ |
| `lerobot-dataset-viz` 등 시각화 유틸 | ❌ (제외) |

### 6. `[tool.setuptools.packages.find]` — `where` 경로

| | upstream | orin |
|---|---|---|
| `where` | `["src"]` | `["."]` |
| 이유 | upstream: `src/lerobot/` 구조 | orin: `orin/lerobot/` 직접 위치 |

### 7. 도구 설정 섹션 — 전면 제거

orin에 없는 섹션:

- `[tool.ruff]` — 린터 (개발 환경 전용)
- `[tool.mypy]` — 타입 체커 (개발 환경 전용)
- `[tool.bandit]` — 보안 스캐너
- `[tool.typos]` — 맞춤법 검사기

---

## 변경 이력

### [2026-04-23] 초기 작성 + torch 의존성 관리 방식 변경

**변경 전 (orin/pyproject.toml):**
```toml
dependencies = [
    "torch>=2.5,<2.7",
    "torchvision>=0.20.0,<0.22.0",
    ...
]
```

**변경 후:**
```toml
dependencies = [
    # torch / torchvision 은 setup_env.sh 에서 jp6/cu126 인덱스로 직접 설치
    # — pyproject 에 두면 pip 가 PyPI CPU-only wheel 로 덮어쓰기 때문
    ...
]
```

**변경 이유:**  
`pip install -e orin/[smolvla,hardware,feetech]` 실행 시 pip 의존성 해석기가 `torch>=2.5,<2.7` 조건을 만족하는 가장 접근하기 쉬운 wheel인 PyPI aarch64 CPU-only torch 2.6.0을 선택하여 jp6/cu126에서 설치한 CUDA-enabled wheel을 덮어썼다.  
`torch.version.cuda = None` + `cuda.is_available() = False`로 확인됨.

**대응:**  
`setup_env.sh`에서 lerobot 설치 *이후* torch를 `--force-reinstall --no-deps`로 재설치하도록 순서 변경.

### [2026-04-23] `[project.scripts]` — upstream 전체 동기화

**변경 전:** `lerobot-eval`, `lerobot-teleoperate` 2개만 등록

**변경 후:** `lerobot-calibrate`, `lerobot-find-port`, `lerobot-find-cameras`, `lerobot-find-joint-limits`, `lerobot-record`, `lerobot-replay`, `lerobot-setup-motors`, `lerobot-teleoperate`, `lerobot-eval`, `lerobot-train`, `lerobot-info` 11개 등록

**변경 이유:** Orin에서 `lerobot-find-port`, `lerobot-calibrate` 등 CLI를 실행하려 했으나 `bash: command not found` 발생. orin의 스크립트 디렉토리(`orin/lerobot/scripts/`)에 upstream scripts를 복사하고 pyproject.toml에 엔트리포인트를 추가함. upstream과 동일하게 유지한다는 원칙에 따라 의존성 문제가 없는 스크립트는 그대로 등록.

**함께 변경된 파일:** `orin/lerobot/scripts/` — upstream 18개 파일 전체 복사 (기존 수정 파일 없음, 덮어쓰기 안전)

---

### [2026-04-30] `[project.scripts]` — `lerobot-eval` / `lerobot-train` entrypoint 제거 (04 TODO-O2)

**대상 파일:** `orin/pyproject.toml` `[project.scripts]` 섹션

**변경 내용:**

```toml
# 제거된 2줄
lerobot-eval              = "lerobot.scripts.lerobot_eval:main"
lerobot-train             = "lerobot.scripts.lerobot_train:main"

# 주석으로 대체 (이력 명시)
# lerobot-eval, lerobot-train 제거 (04 TODO-O2): Orin 은 추론 + 데이터 수집 전용.
# 학습은 DGX, 평가는 hil_inference.py 또는 DGX 가 대체. 변경 이력은 02_orin_pyproject_diff.md 참조.
```

**변경 이유:**

04_infra_setup 마일스톤의 4-노드 아키텍처 도입 (devPC + DataCollector(신규) + DGX + 시연장 Orin) 에 따라 Orin 의 책임이 **추론 전용** 으로 축소. 학습은 DGX, 평가는 `hil_inference.py` 또는 DGX 가 대체. 두 entrypoint 는 사용자가 호출할 일 없음.

**원칙 — 옵션 B (논리적 비활성화):**

`orin/lerobot/scripts/lerobot_eval.py` / `lerobot_train.py` 파일 자체는 **upstream 보존 원칙대로 그대로 유지** (제거 안 함). pyproject.toml 의 entrypoint 등록 해제만으로 사용자 호출 차단. 사유: upstream 동기화 부담 ↓.

**대응:**

- `orin/pyproject.toml [project.scripts]` 에서 2줄 제거
- 본 변경 이력 기록 (본 문서)
- 변경 후 Orin venv 재설치 (`pip install -e .` 재실행) 필요 — TODO-O3 (회귀 검증) 단계에서 처리

**영향 범위:**

| 기능 | 영향 |
|---|---|
| `lerobot-eval` CLI 호출 | ❌ (Orin 에서 더 이상 호출 안 됨, DGX 또는 hil_inference.py 대체) |
| `lerobot-train` CLI 호출 | ❌ (Orin 에서 더 이상 호출 안 됨, DGX 가 학습 담당) |
| `orin/lerobot/scripts/lerobot_eval.py` 파일 자체 | 유지 (upstream 보존) |
| `orin/lerobot/scripts/lerobot_train.py` 파일 자체 | 유지 (upstream 보존) |
| 기존 9개 entrypoint | 영향 없음 |

**잔여 리스크:** upstream 동기화 시 본 entrypoint 정리가 덮어씌워질 수 있음 — BACKLOG 04 #1 로 추적.

---

### [2026-04-23] numpy 범위 — 1.x 전용으로 고정

**변경 이력:**
- 1차: `"numpy>=2.0.0,<2.3.0"` → `"numpy>=1.24.0,<2.3.0"` (하한 완화)
- 2차: `"numpy>=1.24.0,<2.3.0"` → `"numpy>=1.24.0,<2.0.0"` (상한 강화)

**최종값:** `"numpy>=1.24.0,<2.0.0"`

**변경 이유:**  
torch 2.5.0a0+872d972e41.nv24.08 (NVIDIA JP 6.0 wheel)이 NumPy 1.x 로 컴파일됨.  
NumPy 2.x 설치 시 ABI 불일치 경고(`Failed to initialize NumPy`) 발생 및 `torch.from_numpy()` 등 연동 불가.  
1차 변경(`<2.3.0`)은 pip 가 여전히 2.2.6을 선택하여 효과 없었음.  
2차 변경(`<2.0.0`)으로 pip 가 1.x 최신(1.26.4)을 선택하도록 강제.

---

## upstream 동기화 시 재확인 항목

upstream `pyproject.toml`이 업데이트될 때 아래 항목이 orin에 영향을 주는지 확인한다.

- [ ] `requires-python` 상한 추가 여부 (예: `<3.11`) — orin `>=3.10`과 충돌 가능성
- [ ] `torch` / `torchvision` 버전 범위 변경 → jp6/cu126 제공 버전과 호환성 재확인
- [ ] `smolvla` extra 내 `transformers` 버전 변경 → orin `transformers==5.3.0`과 불일치 여부
- [ ] 신규 패키지 추가 → aarch64 / cp310 빌드 존재 여부 확인
- [ ] `[project.scripts]` 변경 → upstream에 새 스크립트 추가 시 orin에도 반영 필요
