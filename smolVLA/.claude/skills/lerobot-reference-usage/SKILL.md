---
name: lerobot-reference-usage
description: 레퍼런스 (lerobot upstream, seeed-lerobot) 활용 규칙. task-executor 가 코드 구현 전 반드시 읽고 따라야 할 절차. 동일·유사 구현 발견 시 그것 기반 작성, 없으면 SKILL_GAP 보고. TRIGGER when 워커가 코드 구현을 시작할 때.
---

# Lerobot Reference Usage

본 스킬은 task-executor 가 코드 구현 전 반드시 따라야 할 **레퍼런스 활용 규칙**.

## 핵심 원칙

> **레퍼런스에 동일·유사 구현이 있으면 반드시 그것을 기반으로 작성한다. 없으면 SKILL_GAP 보고하고 사용자 답 기다린다.**

→ 추측·가정으로 신규 코드 작성 X. 모든 신규 자산은 레퍼런스 기반 또는 사용자 명시 동의 필요.

## 레퍼런스 위치

| 레퍼런스 | 위치 | 용도 |
|---|---|---|
| HuggingFace lerobot upstream | `docs/reference/lerobot/` | 기본 구조·API·patterns |
| Seeed lerobot fork | `docs/reference/seeed-lerobot/` | SO-ARM·하드웨어 특화 |
| reComputer Jetson | `docs/reference/reComputer-Jetson-for-Beginners/` | Jetson 환경 셋업 |
| NVIDIA Jetson 공식 | `docs/reference/nvidia_official/` | PyTorch 설치 |
| Seeed wiki SO-101 | `docs/reference/seeedwiki/` | SO-101 하드웨어 |

⚠️ 모든 레퍼런스는 **read-only** (Hard Constraints Category A — 수정 시도 X. PreToolUse hook 차단됨).

## 작업 흐름

### 1. 구현 시작 전 — 레퍼런스 검색

todo 에 명시된 기능·API 가 레퍼런스에 이미 있는지 확인:

```bash
# 키워드 검색
grep -rn "<keyword>" docs/reference/lerobot/src/
grep -rn "<keyword>" docs/reference/seeed-lerobot/

# 패턴 매칭
find docs/reference/lerobot/ -name "*.py" | xargs grep -l "<pattern>"
```

### 2. 발견 시 — 그 기반 작성

- 레퍼런스 파일을 **반드시 직접 Read** (Grep 으로 파일 존재 확인만으로 부족 — 파일 내용 전체 또는 해당 함수·클래스 직접 Read)
- Read 한 레퍼런스의 **핵심 인터페이스 (함수 시그니처·인자명·기본값·경로) 를 01_implementation.md 에 인용**
- 같은 패턴으로 `orin/` 또는 `dgx/` 에 구현
- 변경 사항 명시 (왜 그대로 안 쓰고 일부 변경했는지)

01_implementation.md 의 `## 적용 룰` 섹션에 명시 예시:

```
- 레퍼런스 직접 Read: docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py
  인용: `def record(..., single_task: str, ..., push_to_hub: bool = True, ...)` (line 47)
- 적용: 위 시그니처 그대로 활용. 변경 사항: Orin 환경에 맞춰 Y 부분만 추가
```

**"레퍼런스를 확인했다" 만으로 부족** — 인용 없이 적용 룰 작성 X. 04_infra_setup TODO-M1 cycle 1 처럼 "스킬 적용 완료" 선언만 하고 실제 인자를 추측 작성한 경우 code-tester 가 Critical 마킹하므로 사전 차단 필수.

### 3. 미발견 시 — SKILL_GAP 보고

레퍼런스에 없는 신규 자산이 필요하면:

1. **즉시 작업 보류** — 추측 작성 X
2. `docs/work_flow/specs/ANOMALIES.md` 활성 spec 섹션에 항목 추가:
   ```
   YYYY-MM-DD HH:MM | [SKILL_GAP] | task-executor:<TODO-XX> | "<무엇이 필요한지>" — 레퍼런스에 동일 구현 없음, 신규 작성 필요
   ```
3. orchestrator 에 보고 (자율 진행 X)

→ orchestrator 가 사용자에게 묻고 답 받은 뒤 작업 재개.

## 흔한 패턴 예시

### Camera 인터페이스
- upstream: `docs/reference/lerobot/src/lerobot/cameras/`
- 우리: `orin/lerobot/cameras/` 에 같은 패턴

### Robot 클래스
- upstream: `docs/reference/lerobot/src/lerobot/robots/`
- 우리: `orin/lerobot/robots/so_follower/`

### Policy
- upstream: `docs/reference/lerobot/src/lerobot/policies/smolvla/`
- 우리: `orin/lerobot/policies/smolvla/`

### Teleoperator
- upstream: `docs/reference/lerobot/src/lerobot/teleoperators/`
- 우리: `orin/lerobot/teleoperators/so_leader/`

## 위반 패턴 (code-tester 가 Critical 마킹)

- ❌ 레퍼런스 검색 없이 신규 코드 작성
- ❌ 레퍼런스에 유사 구현 있는데 그것 무시하고 다른 패턴 사용
- ❌ SKILL_GAP 보고 없이 신규 자산 만든 경우
- ❌ 레퍼런스 파일을 Read 하지 않고 "레퍼런스 적용 완료" 명시 (선언과 실제 행위 불일치)
- ❌ 인자명·기본값·경로를 추측으로 작성하여 실제 레퍼런스와 불일치

→ code-tester 가 발견 시 `MAJOR_REVISIONS` verdict + Critical 마킹.

## ANOMALY 누적 가이드

| 상황 | TYPE |
|---|---|
| 신규 자산 필요 — 레퍼런스 미존재 | `SKILL_GAP` |
| 같은 영역에서 SKILL_GAP 반복 | reflection 이 보강 제안 (skill 내용 보강 또는 신규 skill) |

## Reference

- `/CLAUDE.md` § Hard Constraints Category A (`docs/reference/` 수정 금지)
- 옛 워크플로우 "레퍼런스 활용 규칙" — `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 의 "## 핸드오프 프롬프트 출력 규칙" 부분
