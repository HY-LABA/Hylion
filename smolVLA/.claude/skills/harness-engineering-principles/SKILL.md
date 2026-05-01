---
name: harness-engineering-principles
description: OpenAI harness engineering 원칙 + Martin Fowler 의 가이드/센서 모델. 자기-진화 분석 시 사이클 데이터를 평가하는 평가 프레임워크. TRIGGER when reflection 에이전트가 사이클 회고·갱신 제안을 도출할 때.
---

# Harness Engineering Principles

본 스킬은 reflection 에이전트가 사이클 분석 시 적용할 평가 프레임워크. OpenAI 의 5개월 100만 LOC 실험 + Martin Fowler 의 Harness Engineering 글 + 우리 smolVLA 시스템 검증 결과를 통합.

> 출처: [openai.com/index/harness-engineering](https://openai.com/index/harness-engineering/), [martinfowler.com/articles/harness-engineering.html](https://martinfowler.com/articles/harness-engineering.html)

## 핵심 정의

**Harness** = AI 에이전트의 모든 것에서 **모델 자체를 제외한 인프라** (Birgitta Böckeler).

자기-진화의 목표: **"무엇이 누락되어 있으며, 에이전트가 읽기 쉽고 실행 가능하게 만들려면 어떻게 해야 할까?"** 라는 질문에 매 사이클 답하는 것.

## 2종 컨트롤 모델

| 종류 | 정의 | 우리 시스템에서 |
|---|---|---|
| **Feedforward 가이드** | 행동 *전* 에 안내 | CLAUDE.md, skill, agent system prompt, planner |
| **Feedback 센서** | 행동 *후* 에 자가 수정 | code-tester, prod-test-runner, reflection, ANOMALIES |

## 2종 실행

| 실행 종류 | 특징 | 우리 시스템 |
|---|---|---|
| **Computational** | 결정적·빠름 (ms~s) | PreToolUse hook, pytest, ruff, mypy |
| **Inferential** | LLM 기반·느림 | code-tester, prod-test-runner, reflection |

## 3 규제 카테고리

| 카테고리 | 의미 | 우리 시스템 강도 |
|---|---|---|
| **Maintainability** | 내부 코드 품질 | 🟢 강함 — code-tester |
| **Architecture Fitness** | 아키텍처 invariant 검사 | 🟡 약함 — Coupled File Rules 만 (보강 후보) |
| **Behaviour** | 기능적 정확성 | 🟢 강함 — prod-test-runner + 사용자 검증 |

## OpenAI 핵심 원칙 (체크리스트)

reflection 분석 시 다음 원칙 위반·미반영 발견하면 갱신 제안 도출:

### 1. AGENTS.md / CLAUDE.md = 백과사전 X, 목차

- **안티패턴**: 거대 단일 파일에 모든 지침
- **이유**:
  - 컨텍스트 희소 자원 → 패턴 매칭 fallback
  - "모든 게 중요" → 중요한 게 없어짐
  - 낡은 규칙의 무덤 → 유지 안 됨
- **현재 우리**: CLAUDE.md ~250줄 (양호)
- **점검**: CLAUDE.md 가 한 문장 추가될 때마다 진짜 헌법 수준인지 vs skill 로 빠질 수 있는지 판단

### 2. Progressive Disclosure (점진적 공개)

- 짧은 진입점 (CLAUDE.md) → 깊이는 분산 (skill, context/README, specs/README, agent .md)
- 에이전트가 부담 없이 작은 안정 진입에서 시작 → 다음 단계
- **점검**: 각 워커가 작업 시작 시 적정량의 컨텍스트만 로드하는지

### 3. 에이전트 가독성 — "보이지 않는 지식 X"

> 실행 중 컨텍스트 내 액세스 불가 = 사실상 존재 X

- 사람 머릿속·Slack·Google Docs 의 지식은 시스템에서 안 보임
- 모든 정책·원칙·결정 → 리포 내 버전 관리되는 .md
- **점검**: 사이클 중 워커가 "추측" 또는 "사용자에게 물어봄" 패턴이 자주 발생 → 그 지식이 어디에 명시 안 됐는지

### 4. 황금 원칙 + 정기 가비지 컬렉션

- "기술 부채 = 고금리 대출. 매일 포착·해결"
- 기존 패턴 (불균일·비최적) 도 에이전트가 복제 → 드리프트 필연
- **OpenAI 사례**: Codex 백그라운드 작업이 정기적으로 편차 검사 + 품질 등급 갱신 + 리팩터링 PR 자동
- **현재 우리**: reflection (사이클 종료 시만)
- **점검**: 사이클 내에서 반복된 동일 anomaly → 정기 백그라운드 자동화 후보

### 5. 맞춤형 린터 + 오류에 수정 지침 주입

- 일반 린터 (ruff·mypy) + **도메인 특화 린터** (예: 옵션B 위반 정적 검사)
- 린트 오류 메시지 자체에 "어떻게 고쳐야 하는지" 안내
- **현재 우리**: code-tester (LLM) 만, 정적 검증 약함
- **점검**: code-tester 가 자주 잡는 패턴 중 결정적 룰로 변환 가능한 것 찾기

### 6. "YOLO-style" 데이터 탐색 금지

- 경계에서 데이터 형태 검증 (typed SDK, schema)
- 에이전트가 추측한 모양 위에 빌드 X
- **현재 우리**: lerobot-reference-usage 스킬 일부만 (레퍼런스 우선)
- **점검**: typed SDK / 스키마 검증 의무 사례 발견되면 스킬·hook 보강

### 7. Architecture Fitness Functions

- OpenAI: Types → Config → Repo → Service → Runtime → UI 레이어
- 의존성 방향 + 허용 에지 → 맞춤형 린터·구조 테스트로 강제
- **현재 우리**: orin/lerobot=inference-only, dgx/lerobot=training-only 같은 invariant 명시 X
- **점검**: 도메인 fitness function 후보 식별 → 자동 검증 가능한가

### 8. 자체 구현 선호 (지루한 기술)

- 공개 라이브러리 추상화의 불투명함보다 자체 구현이 에이전트 가독성↑
- 결합성·API 안정성·학습 분포 내 표현
- **우리 환경 다름**: lerobot upstream 위에 쌓는 구조 (옵션B 보존)
- **점검**: 자체 구현으로 더 잘 모델링되는 부분이 있다면 후보 제시

### 9. 최소 차단 병합 게이트

- PR 수명 짧음, 테스트 불안정성 → 후속 실행으로 흡수
- "수정 비용 저렴, 대기 시간 비쌈"
- **현재 우리**: code-tester 2 cycle, prod-test 재시도 — 부분 부합
- **점검**: 사이클 내에서 차단 게이트가 너무 많아 처리량 떨어진 경우 발견

### 10. 사람 입력의 방향성

> 좋은 harness 는 사람 제거 X, **가장 중요한 곳으로 유도**

사람의 unique 가치:
- 조직 메모리
- "load-bearing 컨벤션 vs 단순 습관" 판단

**현재 우리**: Phase 1 spec 작성 + Phase 3 실물 검증 + reflection 갱신 승인
- **점검**: 사람 개입이 본질적 가치 있는 곳인지 vs 자동화 가능한데 빠진 건지

## 우리 시스템의 알려진 보강 후보 (검증 결과)

reflection 분석 시 다음을 우선 살펴볼 영역:

1. **맞춤형 도메인 린터** — 옵션B·Coupled File 정적 검증 (현재 LLM code-tester 만)
2. **품질 등급 시스템** — `docs/QUALITY_SCORE.md` 신설 후보, 도메인별 격차 추적
3. **Architecture Fitness Functions** — orin/dgx 책임 invariant 명시 + 자동 검증
4. **doc-gardening 정기 자동화** — reflection 사이클 외에 주 1회 cron/loop 형태
5. **Memory 시스템 활용** — Claude Code 빌트인 메모리 (`~/.claude/projects/<proj>/memory/`)
6. **Typed SDK 강화** — 코드 경계 검증 의무
7. **Pre-commit "quality left"** — task-executor 작성 직후 자체 ruff·mypy
8. **Continuous monitoring** — Orin 운영 중 latency·정확도 회귀 감지
9. **Hard Constraints 에 "YOLO 금지" 명시** — 경계 검증 또는 typed SDK 의존
10. **취향(taste) 시스템화** — 사용자 자연어 피드백 → 문서·hook·skill 자동 인코딩

## reflection 분석 시 활용

본 스킬을 Read 한 후, 사이클 자료 (context/history, ANOMALIES, BACKLOG) 분석 시:

1. **각 anomaly 가 위 10 원칙 중 어느 것의 위반인지 매핑**
   - 예: SKILL_GAP 반복 → "에이전트 가독성 (3번)" 위반 → 해당 지식을 .md 로 명시 제안
2. **현재 약한 영역 (위 10 보강 후보) 에 해당하는 패턴 발견 시 우선 제안**
3. **사람 개입 빈도 분석** — 너무 잦으면 자동화 후보, 너무 적으면 가드레일 점검 후보

## 핵심 인용 (원문)

- "엔지니어링 팀의 주요 업무는 에이전트가 유용한 업무를 수행할 수 있도록 지원하는 것"
- "Codex에 1,000페이지의 설명서가 아닌 맵을 제공"
- "에이전트의 관점에서 보면 실행 중에 컨텍스트 내에서 액세스할 수 없는 것은 사실상 존재하지 않는 것"
- "구현을 세세하게 관리하지 않고 불변 조건을 강제 적용"
- "기술 부채는 고금리 대출과 같아서 조금씩 꾸준히 갚아나가는 편이 훨씬 낫다"
- "사람의 취향은 한 번 포착되면 코드의 모든 라인에 지속적으로 반영"
