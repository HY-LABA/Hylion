---
name: lerobot-upstream-check
description: lerobot 옵션 B 원칙 (upstream 보존) + Coupled File Rules. orin/lerobot, dgx/lerobot, pyproject.toml 변경 시 동시 갱신 절차. TRIGGER when 워커가 lerobot upstream 영향 영역(Category B)을 작업할 때.
---

# Lerobot Upstream Check

본 스킬은 `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 같은 **upstream 영향 영역** 변경 시 적용해야 할 룰을 정의. task-executor·code-tester·prod-test-runner 가 본 영역 작업 시 반드시 따라야 함.

## 옵션 B 원칙 (upstream 보존)

`orin/lerobot/` 와 `dgx/lerobot/` 의 파일·디렉터리는 **변경하지 않는다**. inference-only 책임 외 모듈은 다음으로만 비활성화:

1. `__init__.py` 의 import 차단
2. `pyproject.toml [project.scripts]` 의 entrypoint 등록 해제

이유: upstream (HuggingFace lerobot) 동기화 부담 ↓.

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

## 변경 시 체크리스트

- [ ] 옵션 B 원칙 준수 (upstream 디렉터리·파일 보존)?
- [ ] Coupled file 동시 갱신 (위 1·2·3 중 해당)?
- [ ] 변경 이력 (.md 파일) 에 날짜·이유·영향 명시?
- [ ] entrypoint 비활성화는 `pyproject.toml [project.scripts]` 에서만?

## 위반 패턴 (code-tester 가 Critical 마킹할 것)

- ❌ orin/lerobot/ 의 새 파일 추가 (옵션 B 위반)
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
