# TODO-X4 — Implementation (1단계: 조사 + 변경 안)

> 작성: 2026-05-02 | task-executor | cycle: 1
> 본 dispatch 는 **1단계 조사·변경 안 작성만** — `dgx/pyproject.toml` 미변경 상태 유지.

## 목표

`dgx/pyproject.toml` 에 record / hardware / feetech 3 extras + 9 entrypoint 추가 (Category B awaits_user I 발송용 조사 완료)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/context/todos/X4/01_implementation.md` | 신규 | 조사 결과 + 변경 안 + awaits_user I 발송 명세 |
| `dgx/pyproject.toml` | **미변경** | Category B 사용자 동의 후 X4 재dispatch 에서 수정 |

## 적용 룰

- CLAUDE.md Hard Constraints Category B: `pyproject.toml` 수정 → 사용자 동의 필수. 본 dispatch 에서 수정 X.
- lerobot-reference-usage: `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` 직접 Read + 인용.
- lerobot-upstream-check: Coupled File Rule 1 — pyproject.toml 수정 시 `setup_train_env.sh` 동시 갱신 필요 (X5 todo 로 분리 처리).
- 레퍼런스 직접 Read: `docs/reference/lerobot/pyproject.toml` (line 97~108 dataset/hardware/feetech extras), `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` (line 40~61 record/hardware/feetech).

---

## §1 torchcodec 호환성 조사 결과

### 1-1. DGX 환경 확인 (docs/storage/06_dgx_venv_setting.md 실측)

| 항목 | 값 | 출처 |
|---|---|---|
| Python | 3.12.3 | DGX 시스템 |
| PyTorch | 2.10.0+cu130 | setup_train_env.sh §2 |
| CUDA | 13.0 | DGX 드라이버 580.142 |
| lerobot 설치 방식 | editable submodule `docs/reference/lerobot/` | setup_train_env.sh §3 |
| extras 현재 | `[smolvla,training]` | setup_train_env.sh line 66 |
| **pyproject.toml 파일** | **미존재** | `dgx/` 하위 없음 — `setup_train_env.sh` 가 직접 lerobot submodule editable 설치 |

> **핵심 발견**: `dgx/` 에는 별도 `pyproject.toml` 이 없다. DGX 는 `setup_train_env.sh` 에서 `pip install -e "${LEROBOT_SRC}[smolvla,training]"` 로 lerobot upstream submodule 을 직접 설치하는 구조. X4 의 "dgx/pyproject.toml 추가" 는 **신규 파일 생성** 이다.

### 1-2. torchcodec 호환 매트릭스 (WebFetch: PyPI + GitHub releases + PyTorch wheel 인덱스)

| torchcodec | 호환 PyTorch | Python | cu130 wheel |
|---|---|---|---|
| 0.9.x | 2.9 | >=3.10 | 미확인 |
| **0.10.0** | **2.10** | **>=3.10, <=3.14** | **존재** (`torchcodec-0.10.0+cu130-cp312-cp312-manylinux_2_28_x86_64.whl`) |
| 0.11.x | 2.11 | >=3.10 | 기본 (0.11.0 부터 Linux 기본값 cu130) |

**확인 근거** (PyTorch wheel 인덱스 `download.pytorch.org/whl/cu130/torchcodec/` WebFetch):
- `torchcodec-0.10.0+cu130` wheel 이 `linux_x86_64`, Python 3.10~3.14 모두 제공됨
- GitHub releases 에서 "torchcodec 0.10.0 is compatible with torch 2.10" 명시 확인
- 0.11.0 부터는 "Linux default = cu130 wheel" 로 변경됨 (즉 0.11.0 = PyTorch 2.11 용)

### 1-3. 호환 결론

**torchcodec 0.10.0 은 DGX PyTorch 2.10.0+cu130 과 호환 가능**.

설치 시 반드시 cu130 인덱스 지정 필요:
```bash
pip install torchcodec==0.10.0 --index-url https://download.pytorch.org/whl/cu130
```

단, `datacollector/pyproject.toml` 의 버전 범위 `>=0.3.0,<0.11.0` 는 0.10.0 을 포함한다. **0.11.0 부터는 PyTorch 2.11 요구 → 상한 `<0.11.0` 유지가 안전**.

### 1-4. lerobot upstream `dataset` extras 의 torchcodec 조건식 확인

`docs/reference/lerobot/pyproject.toml` line 102:
```
"torchcodec>=0.3.0,<0.11.0; sys_platform != 'win32' and (sys_platform != 'linux' or (platform_machine != 'aarch64' and platform_machine != 'arm64' and platform_machine != 'armv7l')) and (sys_platform != 'darwin' or platform_machine != 'x86_64')"
```

→ **linux x86_64 에서 적용됨** (aarch64/arm64/armv7l 제외 조건이므로 x86_64 는 포함).
→ DGX 는 Linux x86_64 이므로 torchcodec 이 자동 설치됨.
→ cu130 인덱스 지정은 `setup_env.sh` 레벨에서 처리해야 함 (pyproject 에서는 인덱스 URL 지정 불가).

### 1-5. setup_env.sh 에서의 torchcodec 별도 설치 필요성

`pip install -e ".[record,hardware,feetech]"` 만으로는 torchcodec 가 PyPI 일반 인덱스에서 CPU-only 또는 잘못된 버전이 설치될 수 있음. X5 에서 다음 패턴 적용 필요:
```bash
pip install torchcodec==0.10.0 --index-url https://download.pytorch.org/whl/cu130
```

---

## §2 의존성 변경 안

### 2-1. 구조적 결정: dgx/pyproject.toml 신규 생성

DGX 에는 현재 `pyproject.toml` 이 없으므로, X4 는 **신규 파일 생성** 이다. 구조는 datacollector 와 동일하게 lerobot submodule 래퍼로 작성.

> 단, DGX 의 lerobot editable 설치는 `setup_train_env.sh` 가 `pip install -e "${LEROBOT_SRC}[smolvla,training]"` 로 처리 중 — X4 의 pyproject.toml 은 **추가 extras 정의 전용** 파일이 아니라, lerobot 설치 전반을 래퍼로 통합하는 파일이다. 따라서:
> - option A: `dgx/pyproject.toml` 신규 생성 + `setup_train_env.sh` 를 `pip install -e "dgx/[record,hardware,feetech]"` 로 재설계
> - option B: `setup_train_env.sh` 에서 `pip install -e "${LEROBOT_SRC}[smolvla,training,dataset,hardware,feetech]"` 로 추가 — pyproject.toml 불필요
>
> **본 조사 제안: Option B** — 이미 lerobot submodule editable 설치 구조가 있으므로 extras 만 확장하는 것이 단순함. `dgx/pyproject.toml` 신규 생성은 오히려 중복 관리 부담을 만든다. X4 DOD 의 "dgx/pyproject.toml 갱신" 을 Option B 방식으로 재해석하면 **pyproject.toml 생성 X + setup_train_env.sh 만 수정** 이 됨.
>
> **사용자 결정 필요**: Option A (pyproject.toml 신규 생성) vs Option B (setup_train_env.sh extras 추가만) — awaits_user I 에 포함.

### 2-2. record extras 패키지 목록 (안)

datacollector/pyproject.toml line 40-47 인용 + torchcodec 버전 범위 유지:

```toml
record = [
    "datasets>=4.0.0,<5.0.0",
    "pandas>=2.0.0,<3.0.0",
    "pyarrow>=21.0.0,<30.0.0",
    "av>=15.0.0,<16.0.0",
    "torchcodec>=0.3.0,<0.11.0; sys_platform == 'linux' and platform_machine == 'x86_64'",
    "jsonlines>=4.0.0,<5.0.0",
]
```

> 변경점: datacollector 원본의 `sys_platform == 'linux' and platform_machine == 'x86_64'` 조건 유지.
> torchcodec 은 pyproject 에서 cu130 인덱스 지정 불가 → X5 setup_env.sh 에서 별도 설치 (§1-5 참조).

### 2-3. hardware extras 패키지 목록 (안)

datacollector/pyproject.toml line 50-54 그대로:

```toml
hardware = [
    "pynput>=1.7.8,<1.9.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]
```

### 2-4. feetech extras 패키지 목록 (안)

datacollector/pyproject.toml line 57-61 그대로:

```toml
feetech = [
    "feetech-servo-sdk>=1.0.0,<2.0.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]
```

### 2-5. 9 entrypoint 목록 (안)

datacollector/pyproject.toml line 70-78 그대로:

```toml
[project.scripts]
lerobot-calibrate         = "lerobot.scripts.lerobot_calibrate:main"
lerobot-find-cameras      = "lerobot.scripts.lerobot_find_cameras:main"
lerobot-find-port         = "lerobot.scripts.lerobot_find_port:main"
lerobot-find-joint-limits = "lerobot.scripts.lerobot_find_joint_limits:main"
lerobot-record            = "lerobot.scripts.lerobot_record:main"
lerobot-replay            = "lerobot.scripts.lerobot_replay:main"
lerobot-setup-motors      = "lerobot.scripts.lerobot_setup_motors:main"
lerobot-teleoperate       = "lerobot.scripts.lerobot_teleoperate:main"
lerobot-info              = "lerobot.scripts.lerobot_info:main"
```

> 단, Option B (pyproject.toml 불생성) 선택 시 entrypoint 도 불필요 — lerobot upstream pyproject.toml 이 이미 동일 entrypoint 전부 포함 (확인: `docs/reference/lerobot/pyproject.toml` line 276-290). 즉 lerobot editable 설치만으로 entrypoint 는 이미 등록됨.

### 2-6. 패키지 충돌 사전 grep 결과

**현재 DGX 설치 (`[smolvla,training]`) 의 관련 패키지 버전 범위** vs **추가 예정 record/hardware/feetech 범위**:

| 패키지 | smolvla/training (upstream) | record/hardware/feetech (datacollector) | 충돌 |
|---|---|---|---|
| datasets | `>=4.0.0,<5.0.0` (training→dataset) | `>=4.0.0,<5.0.0` | **동일 — 충돌 없음** |
| pandas | `>=2.0.0,<3.0.0` (dataset) | `>=2.0.0,<3.0.0` | **동일 — 충돌 없음** |
| pyarrow | `>=21.0.0,<30.0.0` (dataset) | `>=21.0.0,<30.0.0` | **동일 — 충돌 없음** |
| av | `>=15.0.0,<16.0.0` (dataset→av-dep) | `>=15.0.0,<16.0.0` | **동일 — 충돌 없음** |
| torchcodec | `>=0.3.0,<0.11.0` (dataset, 조건부) | `>=0.3.0,<0.11.0` | **동일 — 충돌 없음** |
| jsonlines | `>=4.0.0,<5.0.0` (dataset) | `>=4.0.0,<5.0.0` | **동일 — 충돌 없음** |
| opencv-python-headless | `>=4.9.0,<4.14.0` (base deps) | (없음) | 충돌 없음 |
| Pillow | `>=10.0.0,<13.0.0` (base deps) | (없음) | 충돌 없음 |
| pynput | (없음) | `>=1.7.8,<1.9.0` | 신규 추가 — 충돌 없음 |
| pyserial | `>=3.5,<4.0` (hardware/feetech) | `>=3.5,<4.0` | **동일 — 충돌 없음** |
| deepdiff | `>=7.0.1,<9.0.0` (hardware/feetech) | `>=7.0.1,<9.0.0` | **동일 — 충돌 없음** |
| feetech-servo-sdk | `>=1.0.0,<2.0.0` (feetech) | `>=1.0.0,<2.0.0` | **동일 — 충돌 없음** |

> **근거**: lerobot upstream `pyproject.toml` 이미 `hardware`, `feetech`, `dataset` extras 를 동일 버전 범위로 정의하고 있음 (line 97~108, 145). datacollector 는 이 upstream 를 그대로 사용했으므로 완전 일치. **충돌 0건**.

---

## §3 awaits_user I 발송 명세

### 발송 내용 (orchestrator 가 사용자에게 전달할 내용)

---

**[awaits_user I] X4: dgx 의존성 추가 방식 결정 요청**

**배경**: X4 는 DGX 에 데이터 수집용 의존성 (record/hardware/feetech extras) 을 추가하는 작업입니다. 조사 결과를 정리합니다.

**1. torchcodec 호환성 결과: 호환 가능**

| 항목 | 결과 |
|---|---|
| DGX PyTorch | 2.10.0+cu130 |
| 호환 torchcodec | **0.10.0** (cu130 wheel 공식 제공 확인) |
| 설치 URL | `https://download.pytorch.org/whl/cu130` |
| 버전 범위 | `>=0.3.0,<0.11.0` — 0.10.0 포함, 0.11.0 (PyTorch 2.11 용) 제외 안전 |

torchcodec 0.10.0+cu130 wheel 이 `linux_x86_64`, Python 3.12 에 공식 제공됩니다. 단, `pip install` 시 `--index-url https://download.pytorch.org/whl/cu130` 가 필요합니다 (pyproject.toml 에서 인덱스 URL 지정 불가 → X5 setup_env.sh 에서 별도 설치).

**2. 패키지 충돌 grep 결과: 충돌 0건**

추가 예정 12개 패키지 전부가 lerobot upstream 이미 동일 버전 범위 정의 (`dataset`/`hardware`/`feetech` extras). 완전 일치로 충돌 없습니다.

**3. 핵심 결정: pyproject.toml 신규 생성 vs setup_env.sh extras 추가**

DGX 는 현재 `dgx/pyproject.toml` 이 없습니다. lerobot submodule editable 설치(`setup_train_env.sh`) 구조입니다. 두 옵션이 있습니다:

| 옵션 | 방식 | 장점 | 단점 |
|---|---|---|---|
| **A. pyproject.toml 신규 생성** | `dgx/pyproject.toml` 만들고 lerobot 래퍼 + extras 정의 | orin 패턴과 일관성, 의존성 명시적 관리 | 중복 관리 (lerobot upstream pyproject 와 이중 정의) |
| **B. setup_env.sh extras 추가만** | `setup_train_env.sh` 에서 `pip install -e ".[smolvla,training,dataset,hardware,feetech]"` | 단순, 기존 구조 유지, 신규 파일 불필요 | pyproject.toml 없어 의존성 가시성 낮음 |

> lerobot upstream pyproject.toml 에 이미 `dataset`, `hardware`, `feetech` extras 가 동일 버전 범위로 정의되어 있습니다 (line 97~108, 145). Option B 선택 시 entrypoint 도 이미 등록됨 (lerobot upstream pyproject line 276~290).

**사용자 답변 항목**:

1. **동의 여부**: 위 조사 내용 확인 후 X4 진행 동의 / 비동의 (비동의 시 X4·X5 dispatch X)
2. **방식 선택**: Option A (dgx/pyproject.toml 신규 생성) / Option B (setup_env.sh extras 추가만)
   - 권장: **Option B** (단순, 기존 구조 유지)
3. (Option A 선택 시) 파일명: `dgx/pyproject.toml` 고정

---

### §3-1 사용자 답변 후 처리 흐름

| 답변 | 처리 |
|---|---|
| 동의 + Option A | X4 재dispatch: `dgx/pyproject.toml` 신규 생성 (3 extras + 9 entrypoint) |
| 동의 + Option B | X4 재dispatch 불필요. X5 직접: `setup_train_env.sh` 에서 extras 추가 + torchcodec cu130 별도 설치 |
| 비동의 | X4·X5 dispatch 취소, V 그룹에서 record extras 없이 검증 (기존 smolvla,training 만) |

---

## §4 X4 재dispatch 시 작업 범위 (사용자 동의 + Option A 선택 후)

본 절은 사용자 동의 후 실제 `dgx/pyproject.toml` 수정 단계에서 수행할 작업 명세.

### 4-1. 생성할 파일: `dgx/pyproject.toml`

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "lerobot"
version = "0.5.2"
description = "LeRobot curated subset for DGX (train + record, Linux x86_64)"
requires-python = ">=3.12"

# 기본 의존성: lerobot submodule 직접 editable 설치하므로 pyproject 에는 최소 선언.
# 실제 torch / lerobot 설치는 setup_train_env.sh 에서 처리.
dependencies = []

[project.optional-dependencies]
# record: LeRobotDataset 포맷 저장 + HF Hub + 비디오 인코딩
# torchcodec: cu130 wheel 필요 → setup_train_env.sh 에서 별도 설치
record = [
    "datasets>=4.0.0,<5.0.0",
    "pandas>=2.0.0,<3.0.0",
    "pyarrow>=21.0.0,<30.0.0",
    "av>=15.0.0,<16.0.0",
    "torchcodec>=0.3.0,<0.11.0; sys_platform == 'linux' and platform_machine == 'x86_64'",
    "jsonlines>=4.0.0,<5.0.0",
]

# hardware: SO-ARM 모터 제어 + 키보드 입력
hardware = [
    "pynput>=1.7.8,<1.9.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]

# feetech: SO-ARM Feetech 서보 직접 구동
feetech = [
    "feetech-servo-sdk>=1.0.0,<2.0.0",
    "pyserial>=3.5,<4.0",
    "deepdiff>=7.0.1,<9.0.0",
]

[project.scripts]
# 데이터 수집 + 하드웨어 설정 entrypoint
# lerobot-train / lerobot-eval 은 lerobot upstream pyproject 에서 등록됨 (editable 설치)
lerobot-calibrate         = "lerobot.scripts.lerobot_calibrate:main"
lerobot-find-cameras      = "lerobot.scripts.lerobot_find_cameras:main"
lerobot-find-port         = "lerobot.scripts.lerobot_find_port:main"
lerobot-find-joint-limits = "lerobot.scripts.lerobot_find_joint_limits:main"
lerobot-record            = "lerobot.scripts.lerobot_record:main"
lerobot-replay            = "lerobot.scripts.lerobot_replay:main"
lerobot-setup-motors      = "lerobot.scripts.lerobot_setup_motors:main"
lerobot-teleoperate       = "lerobot.scripts.lerobot_teleoperate:main"
lerobot-info              = "lerobot.scripts.lerobot_info:main"

[tool.setuptools.packages.find]
where = ["."]
```

> **주의**: Option A 선택 시 위 pyproject.toml 의 entrypoint 가 lerobot upstream editable 설치 entrypoint 와 충돌할 가능성 — pip install 순서에 따라 덮어쓰기 발생 가능. 사용자 동의 후 재dispatch 에서 실제 설치 테스트로 확인 필요.

### 4-2. Coupled File Rule 1 — setup_train_env.sh 동시 갱신 (X5 에서 처리)

X4 완료 직후 X5 dispatch:
- `setup_train_env.sh §3` 에 record extras 설치 step 추가
- torchcodec cu130 별도 설치 추가

### 4-3. Coupled File Rule — `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 유사 파일

현재 dgx 대응 파일 없음. X4 에서 `dgx/pyproject.toml` **신규 생성** 이므로 diff 파일 생성 필요성 → `docs/storage/lerobot_upstream_check/` 에 `06_dgx_pyproject_diff.md` 신규 작성 (X4 재dispatch 에서 함께 처리).

---

## 변경 내용 요약

본 dispatch 는 `dgx/pyproject.toml` 을 수정하지 않고 사전 조사만 수행했다. 조사 결과:

1. torchcodec 0.10.0+cu130 wheel 이 DGX PyTorch 2.10.0+cu130, Python 3.12, Linux x86_64 에 공식 제공됨 — 호환 가능.
2. 추가 예정 12개 패키지 전부 lerobot upstream 동일 버전 범위 정의 — 충돌 0건.
3. DGX 에 `dgx/pyproject.toml` 이 없는 구조적 특성 발견 — 신규 생성(Option A) vs setup_env.sh 추가만(Option B) 사용자 결정 필요.
4. awaits_user I 발송 내용 (§3) 작성 완료.

## code-tester 입장에서 검증 권장 사항

- lint: 본 dispatch 에서 코드 변경 없음 — 검증 대상 없음
- 문서 정합: §2 의 버전 범위가 `docs/reference/lerobot/pyproject.toml` 및 `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` 와 일치하는지 교차 확인
- torchcodec wheel 존재: `https://download.pytorch.org/whl/cu130/torchcodec/` 에서 `torchcodec-0.10.0+cu130-cp312-cp312-manylinux_2_28_x86_64.whl` 존재 확인 (WebFetch 로 검증 가능)
- 구조적 결정 (Option A vs B): 사용자 답변 후 재dispatch 에서 선택된 옵션 기반 구현

## 직전 피드백 반영 (해당 없음 — 1 cycle)
