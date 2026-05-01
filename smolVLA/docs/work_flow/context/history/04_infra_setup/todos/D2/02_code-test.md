# TODO-D2 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건 (MINOR 기준 3건 미달). DOD 12개 산출물 항목 모두 충족. CLAUDE.md Hard Constraints 위반 없음. D1 R1·R2 권고 완전 반영 확인.

---

## 단위 테스트 결과

```
task 타입 — 신규 .py 파일 없음. pytest 해당 없음.
setup_env.sh 내 Python 검증 블록 (lerobot / torch / datasets / feetech import + entrypoint shutil.which) 은 DataCollector 머신 런타임 검증 — TODO-D3 책임.
```

---

## Lint·Type 결과

```
신규 .py 파일 없음 — ruff / mypy 해당 없음.

bash 문법 (bash -n) 검증:
  SKILL_GAP #1 (Bash 차단) — bash -n 실행 불가.
  시각 검증 실시: set -e, if/elif/fi, case/esac, heredoc (<<'PYEOF', <<'ENVEOF'),
  따옴표, 변수 참조 ($SMOLVLA_DIR, $VENV_DIR, $PYTHON, $LEROBOT_DIR 등) 모두 문법 정상.
  ln -s, grep, cat >> 등 명령 사용 패턴 정상.
  Critical 이슈 없음.

TOML 문법 (tomllib.load) 검증:
  SKILL_GAP #1 (Bash 차단) — tomllib 직접 실행 불가.
  시각 검증 실시: [build-system], [project], [project.optional-dependencies],
  [project.scripts], [tool.setuptools.packages.find] 섹션 구조 정상.
  PEP 508 환경 마커 (; sys_platform == 'linux' and platform_machine == 'x86_64') 문법 유효.
  Critical 이슈 없음.
```

---

## DOD 정합성

| DOD 항목 (spec §D2 + 01_implementation.md 산출물 표) | 충족 | 메모 |
|---|---|---|
| `datacollector/` 신규 디렉터리 (scripts/ tests/ config/ data/) | ✅ | ls 확인 — 4개 하위 디렉터리 존재 |
| `datacollector/pyproject.toml` 신규 | ✅ | record+hardware+feetech extras, 9개 entrypoint, smolvla·training 미정의 |
| `datacollector/scripts/setup_env.sh` 신규 | ✅ | .hylion_collector venv, 표준 PyPI torch, orin 대비 차이 명시 |
| `datacollector/scripts/run_teleoperate.sh` 이관 | ✅ | archive 에서 최종 이관. 이관 이력 헤더 주석 포함 |
| `datacollector/README.md` 신규 | ✅ | 책임, 환경 표, 디렉터리 트리, 관련 문서 포함 |
| `datacollector/tests/README.md` 신규 | ✅ | TODO-G3 이식 예정 명시 + 현재 수동 검증 명령 포함 |
| `datacollector/config/README.md` 신규 | ✅ | ports.json / cameras.json 설명 + git 추적 정책 |
| `datacollector/data/README.md` 신규 | ✅ | HF Hub + rsync 전송 방식 안내 (T1 결정 반영) |
| `05_datacollector_lerobot_diff.md` 신규 (coupled file) | ✅ | 현재 상태 요약, 비활성화 표, orin 대비 차이, 변경 이력 모두 포함 |
| `smolVLA/.gitignore` 신규 | ✅ | datacollector/.hylion_collector/ + datacollector/data/ 패턴 포함 |
| `docs/storage/others/run_teleoperate.sh.archive` 이관 완료 표시 | ✅ | "TODO-D2 최종 이관 완료" 메시지로 갱신 |
| `BACKLOG.md` § [04_infra_setup] #2 "완료" 갱신 | ✅ | "완료 (2026-05-01 TODO-D2: datacollector/scripts/run_teleoperate.sh 로 최종 이관)" 반영 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `datacollector/config/` | D1 §3-2 트리에는 ports.json / cameras.json placeholder 존재로 표현됨. D1 §3-3 책임 표에서는 TODO-G3 시점으로 명시. 현재는 README.md 만 존재. orin/ 패턴 (TODO-O2 에서 null placeholder 신규 작성) 과 불일치. Recommended: TODO-G3 이식 전에 null placeholder 2개 신규 작성 고려 (orin/config/ports.json 패턴 미러). DOD 미정의 항목이므로 Critical 아님. |
| 2 | `smolVLA/.gitignore` | Hylion 루트 `.gitignore` 에 `smolVLA/orin/checkpoints/*/` 패턴 존재. smolVLA/.gitignore (신규) 에는 동일 패턴 미포함. 이중 무시 아닌 단순 일관성 차이 — 기능적 문제 없음 (상위 ignore 가 커버). 스타일 차원에서 smolVLA/.gitignore 에 orin/checkpoints/ 도 추가하면 smolVLA 범위에서 self-contained gitignore 가 됨. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. 변경 파일 모두 허용 영역 (datacollector/, docs/storage/, BACKLOG.md, .gitignore) |
| B (자동 재시도 X 영역) | ✅ / ⚠️ CONSTRAINT_AMBIGUITY | `.gitignore` Category B 해당. 단 smolVLA/.gitignore 는 신규 파일 생성 (기존 파일 수정 아님). CLAUDE.md Category B 는 "변경" 명시 — 신규 파일 생성이 "변경" 범주인지 정책 불명확. 보수적으로 Category B 에 준하는 항목으로 취급. 패턴 내용 검토 결과 합리적 (datacollector/data/ + .hylion_collector/ 필요 패턴 포함). MAJOR 사유 없음. |
| Coupled File Rules | ✅ | `datacollector/lerobot/` 관련 `05_datacollector_lerobot_diff.md` 신규 작성 완료. 옵션 B 원칙 (파일 변경 X) 준수 — `datacollector/lerobot/` 자체 파일 미변경 (setup_env.sh §0-b symlink/rsync 로 처리). |
| C (사용자 동의) | ✅ | 새 디렉터리 (datacollector/), 외부 의존성 추가 (pyproject.toml 신규), 시스템 환경 변경 (.hylion_collector venv) 모두 D1 awaits_user 답변으로 사전 동의 확보 완료. |
| D (절대 금지 명령) | ✅ | setup_env.sh 내 `sudo apt-get install` 는 사용자가 DataCollector 머신에서 직접 실행하는 스크립트의 내용 — AI 워커 Bash 실행과 별개. orin/scripts/setup_env.sh 도 동일 패턴. Category D 미해당. |
| 옛 룰 (`docs/storage/` bash 명령 예시) | ✅ | `docs/storage/` 에 신규 bash 명령 예시 추가 없음. (05_datacollector_lerobot_diff.md 는 변경 이력 문서로 bash 명령 없음) |

---

## D1 R1·R2 권고 반영 확인

| 권고 | 반영 여부 | 확인 위치 |
|---|---|---|
| R1 — `record` 키가 DataCollector 자체 정의 키 (upstream `dataset` 대응) 임을 주석 명시 | ✅ 완전 반영 | `datacollector/pyproject.toml` L36-39: `# record: upstream dataset extras 에 대응 (DataCollector 자체 정의 키)` 주석 + 추가 설명 주석 포함 |
| R2 — torchcodec 조건부 패키지 포함 | ✅ 완전 반영 | `datacollector/pyproject.toml` L45: `"torchcodec>=0.3.0,<0.11.0; sys_platform == 'linux' and platform_machine == 'x86_64'"` 포함 |

---

## 핵심 기술 검증

### torchcodec 조건부 단순화 정확성

upstream 조건: `sys_platform != 'win32' and (sys_platform != 'linux' or (platform_machine != 'aarch64' and platform_machine != 'arm64' and platform_machine != 'armv7l')) and (sys_platform != 'darwin' or platform_machine != 'x86_64')`

DataCollector 단순화: `sys_platform == 'linux' and platform_machine == 'x86_64'`

검증 (DataCollector 타겟 플랫폼별):

| 플랫폼 | upstream 조건 결과 | DataCollector 단순화 결과 | 일치 |
|---|---|---|---|
| x86_64 Linux (DataCollector 타겟) | True (설치됨) | True (설치됨) | ✅ |
| aarch64 Linux (Jetson) | False (설치 안 됨) | False | ✅ |
| macOS Intel (darwin x86_64) | False (설치 안 됨) | False | ✅ |
| Windows | False (설치 안 됨) | False | ✅ |
| arm64 macOS (Apple Silicon) | True (설치됨) | False (설치 안 됨) | ⚠️ 차이 |

arm64 macOS (Apple Silicon) 에서 upstream 은 torchcodec 설치를 허용하지만 DataCollector 조건은 설치하지 않음. 단, DataCollector 는 x86_64 Ubuntu 22.04 전용으로 설계됨 (D1 §1-1 결정). arm64 macOS DataCollector 미지원 가정이 01_implementation.md 에 명시됨. **DataCollector 운영 범위에서 논리적 결함 없음.**

### upstream extras 패키지 값 검증

| 항목 | upstream 기준 | datacollector/pyproject.toml | 일치 |
|---|---|---|---|
| datasets | >=4.0.0,<5.0.0 | >=4.0.0,<5.0.0 | ✅ |
| pandas | >=2.0.0,<3.0.0 | >=2.0.0,<3.0.0 | ✅ |
| pyarrow | >=21.0.0,<30.0.0 | >=21.0.0,<30.0.0 | ✅ |
| av | >=15.0.0,<16.0.0 (av-dep) | >=15.0.0,<16.0.0 | ✅ |
| torchcodec | >=0.3.0,<0.11.0 | >=0.3.0,<0.11.0 | ✅ |
| jsonlines | >=4.0.0,<5.0.0 | >=4.0.0,<5.0.0 | ✅ |
| pynput | >=1.7.8,<1.9.0 (pynput-dep) | >=1.7.8,<1.9.0 | ✅ |
| pyserial | >=3.5,<4.0 (pyserial-dep) | >=3.5,<4.0 | ✅ |
| deepdiff | >=7.0.1,<9.0.0 (deepdiff-dep) | >=7.0.1,<9.0.0 | ✅ |
| feetech-servo-sdk | >=1.0.0,<2.0.0 | >=1.0.0,<2.0.0 | ✅ |

### entrypoint 9개 확인

| entrypoint | pyproject.toml 등록 여부 | 비고 |
|---|---|---|
| lerobot-calibrate | ✅ | |
| lerobot-find-cameras | ✅ | |
| lerobot-find-port | ✅ | |
| lerobot-find-joint-limits | ✅ | |
| lerobot-record | ✅ | |
| lerobot-replay | ✅ | |
| lerobot-setup-motors | ✅ | |
| lerobot-teleoperate | ✅ | |
| lerobot-info | ✅ | |
| lerobot-eval | ❌ 미등록 (의도적) | DataCollector 추론 X |
| lerobot-train | ❌ 미등록 (의도적) | DataCollector 학습 X |

### setup_env.sh — orin 대비 핵심 차이

| 항목 | Orin setup_env.sh | DataCollector setup_env.sh | 부합 |
|---|---|---|---|
| cusparseLt 처리 | 있음 (Jetson 한정) | 없음 | ✅ |
| LD_LIBRARY_PATH 패치 | 있음 | 없음 | ✅ |
| torch 설치 방식 | NVIDIA JP 6.0 redist URL | pip install torch torchvision (표준 PyPI) | ✅ |
| lerobot extras | smolvla+hardware+feetech | record+hardware+feetech | ✅ |
| Python | 3.10 우선 | 3.12 우선 | ✅ |
| venv 이름 | .hylion_arm | .hylion_collector | ✅ |

---

## SKILL_GAP / ANOMALY

| TYPE | 내용 |
|---|---|
| SKILL_GAP #1 | Bash 실행 차단 — `bash -n setup_env.sh` 및 `python3 -c "import tomllib; tomllib.load(...)"` 실행 불가. 시각 검증으로 대체 완료. bash 문법 / TOML 문법 모두 시각 검증에서 이상 없음. 단, 런타임 실행 검증은 TODO-D3 (prod-test-runner) 에서 확인 필요. |
| CONSTRAINT_AMBIGUITY #1 | `smolVLA/.gitignore` 신규 파일 생성이 Category B `.gitignore "변경"` 에 해당하는지 CLAUDE.md 에 명확히 정의되지 않음. 보수적으로 Category B 에 준하는 검토 실시. 패턴 내용 합리성 확인 완료 — Critical 이슈 없음으로 판단. |

---

## 배포 권장

**READY_TO_SHIP — prod-test-runner (TODO-D3) 진입 권장.**

DataCollector 머신 실물 검증 (setup_env.sh 실행 + lerobot import + SO-ARM lerobot-find-port + 카메라 lerobot-find-cameras) 은 TODO-D3 의 책임. 사용자 실물 환경 필요.
