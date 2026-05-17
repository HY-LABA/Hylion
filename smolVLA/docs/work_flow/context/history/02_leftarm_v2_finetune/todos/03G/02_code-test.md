# TODO-03-G — Code Test

> 작성: 2026-05-18 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 1건 (READY 기준 충족).

---

## 단위 테스트 결과

```
pytest 대상 없음 — 본 todo 는 pyproject.toml 의존성 추가 + setup_env.sh 검증 라인 추가 + 문서 갱신.
단위 테스트 대상 Python 모듈 변경 없음 (신규 코드 없음).
```

해당 없음 (코드 로직 변경 없음).

---

## Lint·Type 결과

```
bash -n orin/scripts/setup_env.sh → PASS (exit 0)

python3 -c "import tomllib; with open('orin/pyproject.toml', 'rb') as f: data = tomllib.load(f)" → PASS

smolvla extra 내용 (tomllib 파싱 결과):
  transformers==5.3.0
  num2words>=0.5.14,<0.6.0
  accelerate>=1.7.0,<2.0.0
  peft>=0.18.0,<1.0.0
```

---

## DOD 정합성

TODO-03-G 의 DOD 는 implementation.md 에서 정의됨 (plan.md 에 별도 섹션 없음 — walkthrough 중 ad-hoc 추가 sub-step).

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `orin/pyproject.toml` smolvla extra 에 `peft>=0.18.0,<1.0.0` 추가 | ✅ | tomllib 파싱으로 `peft>=0.18.0,<1.0.0` 존재 확인 |
| 2. 버전 범위가 upstream `peft-dep = ["peft>=0.18.0,<1.0.0"]` (line 134) 와 동일 | ✅ | 그대로 채택. `docs/reference/lerobot/pyproject.toml:134` 직접 확인 완료 |
| 3. torch/torchvision/numpy 미건드림 (Coupled Rule §1 분리 정책) | ✅ | git diff 상 해당 항목 변경 없음. setup_env.sh §3 블록 불변 |
| 4. TOML 문법 정상 | ✅ | tomllib.load() PASS |
| 5. `orin/scripts/setup_env.sh` §6-b 신규 블록 추가 (peft import 검증) | ✅ | 라인 167-169 존재. `bash -n` PASS |
| 6. setup_env.sh 기존 §6 패턴과 일관 (헤더 주석 + echo + python -c) | ✅ | 기존 §6 패턴 동일 구조 (헤더 주석 `# ── 6-b.`, echo "[setup] ...", python -c + `||` 오류 처리) |
| 7. idempotent 유지 (재실행 안전) | ✅ | `python -c "import peft; ..."` 는 순수 import 테스트 — 재실행 시 부작용 없음 |
| 8. `02_orin_pyproject_diff.md` 2026-05-18 신규 entry 추가 | ✅ | `### [2026-05-18] peft 의존성 추가` entry 존재 확인 |
| 9. entry 에 날짜·이유·before/after·버전 근거·영향·출처 포함 | ✅ | 모든 필수 필드 존재 (변경 파일, 변경 내용 before/after, 변경 이유, 버전 범위 근거, 영향, 출처) |
| 10. "현재 차이 요약" §4 smolvla 행 갱신 | ✅ | `peft>=0.18.0,<1.0.0 (직접, 2026-05-18 추가)` 반영됨 |
| 11. `docs/reference/` 미변경 (참조만) | ✅ | git diff Category A 확인: `docs/reference/` 변경 없음 |

---

## Critical 이슈 (없음)

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/scripts/setup_env.sh:169` | `peft import 실패` 에러 메시지에 현재 설치된 버전 범위 (`>=0.18.0,<1.0.0`) 명시 권장 — 사용자 트러블슈팅 시 어느 버전을 설치해야 하는지 즉시 파악 가능. 현재는 "pip install peft>=0.18.0 재시도" 로 충분히 안내되어 있으나 upper bound 미명시. Minor 수준. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 변경 없음. `.claude/` 는 `scheduled_tasks.lock` 삭제만 — task-executor 변경 아님 (git status 기존 D 상태), `.claude/agents/*.md` / `.claude/skills/**/*.md` / `.claude/settings.json` 미변경 |
| B (자동 재시도 X 영역) | ✅ 변경 있음, 사용자 승인 확인 | `orin/pyproject.toml` + `orin/scripts/setup_env.sh` 변경. implementation.md "Category B 사용자 승인 받음 (2026-05-18)" 명시. 최소 면적 원칙 준수 (peft 1줄 추가 + 검증 라인 1줄) |
| Coupled File Rule §1 | ✅ | `orin/pyproject.toml` 변경 + `setup_env.sh` 동시 갱신 확인 |
| Coupled File Rule §2 | ✅ | `orin/pyproject.toml` 변경 + `02_orin_pyproject_diff.md` 동시 갱신 확인 |
| Coupled File Rule §3 | ✅ 해당 없음 | `orin/lerobot/` 코드 변경 없음 — `03_orin_lerobot_diff.md` 갱신 불필요 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `02_orin_pyproject_diff.md` 에 bash 명령 예시 추가 없음 (변경 이력·diff 기록만) |
| lerobot-upstream-check (옵션 B 원칙) | ✅ | `orin/lerobot/` 파일 미변경. upstream peft-dep 버전 범위 그대로 채택. 자체 lock 추가 없음 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 수행 사항 (plan.md Group 2 SSH_AUTO):
- Orin SSH: venv `pip install -e orin/[smolvla,hardware,feetech]` 재실행 → peft 설치 확인
- `python -c "import peft; print(peft.__version__)"` — `>=0.18.0` 확인
- setup_env.sh 재실행 시 §6-b 검증 블록 정상 통과 확인
