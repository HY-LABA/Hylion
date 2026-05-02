---
name: lerobot-upstream-check
description: lerobot 옵션 B 원칙 (upstream 보존) + Coupled File Rules. orin/lerobot, dgx/lerobot, pyproject.toml 변경 시 동시 갱신 절차. TRIGGER when 워커가 lerobot upstream 영향 영역(Category B)을 작업할 때.
---

# Lerobot Upstream Check

본 스킬은 `orin/lerobot/`, `dgx/lerobot/`, `datacollector/lerobot/`, `pyproject.toml` 같은 **upstream 영향 영역** 변경 시 적용해야 할 룰을 정의. task-executor·code-tester·prod-test-runner 가 본 영역 작업 시 반드시 따라야 함.

## 옵션 B 원칙 (upstream 보존)

`orin/lerobot/`, `dgx/lerobot/`, `datacollector/lerobot/` 의 파일·디렉터리는 **변경하지 않는다** (옵션 B 원칙). 단 upstream 이 노드 환경 (Python 버전·플랫폼 등) 과 비호환 syntax 사용 시 해당 파일만
  backport 가능 — 이때 노드별 diff 파일 (예: `05_datacollector_lerobot_diff.md`) 에 변경 이력 의무 기록. inference-only 책임 외 모듈은 다음으로만 비활성화:

1. `__init__.py` 의 import 차단
2. `pyproject.toml [project.scripts]` 의 entrypoint 등록 해제

이유: upstream (HuggingFace lerobot) 동기화 부담 ↓.

## Python 버전 사전 grep 검증

> **사용 시점**: Category B 영역에서 `requires-python` 변경 시 필수.
> `pyproject.toml` 의 `requires-python` 완화는 코드 호환성 보장 X — lerobot upstream 이 PEP 695 등 syntax-level 의존 사용 시 import 시 SyntaxError.

### 검증 명령

```bash
# 1. PEP 695 generic / type alias (Python 3.12+)
grep -rEn "^(def|async def|class) [a-zA-Z_]+\[" docs/reference/lerobot/src/lerobot/
grep -rEn "^type [A-Za-z_]+ ?=" docs/reference/lerobot/src/lerobot/

# 2. match statement (Python 3.10+)
grep -rn "^[ \t]*match " docs/reference/lerobot/src/lerobot/ | head -10

# 3. 공식 declared 버전
grep "requires-python" docs/reference/lerobot/pyproject.toml
grep "Python" docs/reference/lerobot/CLAUDE.md
```

### 해석

| 결과 | 대응 |
|---|---|
| 매치 발견 | 해당 syntax 도입 Python 버전 확인 → `requires-python` 그 이상 강제 |
| 옵션 B 우회 (낮춤) | 매치된 파일 모두 backport 의무 — `orin/lerobot/` 패턴 참조 |
| 공식 버전 ≥ 시스템 Python | 우회 가능 (단 위 grep 결과 0 건이어야) |
| 공식 버전 > 시스템 Python | 우회 X — deadsnakes PPA / uv standalone 등 정공법 |

### 도입 사유

> **05_interactive_cli (2026-05-02)** — `datacollector/pyproject.toml` 의 `requires-python` 을 `>=3.12` → `>=3.10` 완화. `setup_env.sh` 는 통과했으나 lerobot import 시 5+ 파일 PEP 695 SyntaxError. 영향 파일: `utils/io_utils.py:93`, `datasets/streaming_dataset.py:58`, `processor/pipeline.py:255`, `motors/motors_bus.py:51-52`.
>
> **교훈**: `pyproject.toml` 우회 ≠ 코드 호환성. 사전 grep 절차 신설.

## Coupled File Rules (CLAUDE.md § Coupled File Rules 와 일관)

### 1. `orin/pyproject.toml` 수정 시

다음 두 파일 **반드시 동시 갱신**:

#### a. `orin/scripts/setup_env.sh`

- pyproject.toml 의존성 변경이 Orin 설치 스크립트에도 반영되어야 함
- 특히 **torch / torchvision / numpy** 는 pyproject.toml 이 아닌 `setup_env.sh` 에서 직접 관리
  - 사유: Jetson 의 PyTorch wheel 은 NVIDIA redist URL 로 직접 설치해야 함 (PyPI 일반 wheel 은 CPU-only)
- 의존성 추가/제거/버전 변경 → setup_env.sh 의 해당 패키지 명령 갱신

#### b. `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md`

변경 이력 누적 기록:

```markdown
## YYYY-MM-DD — <변경 사유>

**Before**:
```toml
(이전 의존성 항목)
```

**After**:
```toml
(이후 의존성 항목)
```

**Upstream 대비 차이**:
- (현재 우리 pyproject 가 upstream 과 어떻게 다른지)
```

### 2. `orin/lerobot/` 코드 수정 시

#### `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md`

upstream (`lerobot/src/lerobot/`) 대비 변경 이력 누적:

```markdown
## YYYY-MM-DD — <파일 경로> — <변경 사유>

**파일**: `orin/lerobot/.../foo.py`

**변경 이유**: ...

**영향 범위**: 
- 직접 영향: ...
- 간접 영향: ...

**inference-only 트리밍 여부**: yes/no (yes 면 사유 + 트리밍된 기능 명시)
```

### 3. `dgx/lerobot/` 코드 수정 시 (있으면)

`docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` (해당 시 — 현재 미생성 가능성)

### 4. `datacollector/lerobot/` 코드 수정 시 (옵션 B 또는 backport)

`docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` (해당 시 — 본 사이클 시점 미생성. BACKLOG #11 (c) 진행 시 신규 작성 의무).

특히 PEP 695 syntax (Python 3.12+) backport 시:
- 5+ 파일 (`utils/io_utils.py`, `datasets/streaming_dataset.py`, `processor/pipeline.py`, `motors/motors_bus.py`) 후보
- orin 패턴 미러: `def fn[T: ...]` → `TypeVar` + `def fn(... obj: "_T")`, `class C[T]` → `Generic[T]`, `type X = ...` → `Union[...]`
- 향후 lerobot upstream 동기화 시 매번 backport 갱신 부담 명시 (maintenance burden)

## 변경 시 체크리스트

- [ ] 옵션 B 원칙 준수 (upstream 디렉터리·파일 보존)?
- [ ] Coupled file 동시 갱신 (위 1·2·3 중 해당)?
- [ ] 변경 이력 (.md 파일) 에 날짜·이유·영향 명시?
- [ ] entrypoint 비활성화는 `pyproject.toml [project.scripts]` 에서만?

## 위반 패턴 (code-tester 가 Critical 마킹할 것)

- ❌ orin/lerobot/, dgx/lerobot/, datacollector/lerobot/ 의 새 파일 추가 — 단 backport 사유 (Python 버전 비호환 등) + 해당 diff 파일 갱신 시 예외
- ❌ orin/pyproject.toml 변경하면서 setup_env.sh·02_*.md 미갱신
- ❌ orin/lerobot/ 코드 수정하면서 03_*.md 미갱신
- ❌ entrypoint 활성화 (`pyproject.toml [project.scripts]` 에 신규 추가)

→ code-tester 가 발견 시 Critical 분류 → MAJOR_REVISIONS verdict.
→ Category B 영역이라 자동 재시도 X → orchestrator 가 사용자에게 보고.

## ANOMALY 누적 가이드

| 상황 | TYPE |
|---|---|
| 같은 영역에서 동일 위반 반복 | `MAJOR_RETRY` |
| upstream 동기화 후 차이 모호 | `SKILL_GAP` (룰 보강 필요) |

## Reference

- `/CLAUDE.md` § Coupled File Rules (정책 정의)
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` (현재 차이 — 변경 시 반드시 Read)
- `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` (현재 차이)
- `docs/reference/lerobot/` (HuggingFace upstream — read-only)
