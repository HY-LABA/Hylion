# TODO-D1 — Code Test

> 작성: 2026-05-01 15:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 2건 (MINOR 기준인 3건 미달). study 산출물로 단위 테스트·lint 미해당. DOD 5개 절 모두 충족. CLAUDE.md Hard Constraints 위반 없음.

---

## 단위 테스트 결과

study 타입 — 코드 변경 없음. pytest 미해당.

---

## Lint·Type 결과

study 타입 — .py 파일 미작성. ruff / mypy 미해당.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| §1 노드 정체 (하드웨어·OS·네트워크) — 사용자 답 4건 반영 | ✅ | §1-1: 별도 PC 신규·Ubuntu 22.04 LTS·x86_64. §1-2: 시연장 WiFi DHCP. §1-3: placeholder 기재 (실물 구매 전) |
| §2 venv·lerobot 의존성 (orin venv 와의 차이점) | ✅ | §2-1~2-5 완비. Jetson 제약 없음 명시. PyTorch 표준 wheel 언급. extras subset (record+hardware+feetech) + smolvla·training 제외 사유 명확 |
| §3 디렉터리 구조 (orin/ 형제 패턴, hardware + record 책임) | ✅ | §3-1~3-5 완비. 트리 + 컴포넌트 책임 표 + 옵션 B 원칙 + coupled file 의무 명시 |
| §4 시연장 인근 배치 시 고려사항 | ✅ | §4-1 DHCP 리스크 + §4-2 HF Hub 가용 여부 + §4-3 물리 배선 + §4-4 이동 체크리스트 |
| §5 devPC ↔ DataCollector 네트워크 (SSH 설정, ~/.ssh/config) | ✅ | §5-1 SSH config 템플릿 + §5-2 rsync deploy 패턴 + §5-3~5-5 전송 토폴로지 |

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `09_datacollector_setup.md` §2-3 "권장 구성" 코드블록, §2-4 비교표 | `record` 키 이름 혼란 가능성 — 주석 추가 권장 (상세는 아래 "Recommended 상세") |
| 2 | `09_datacollector_setup.md` §2-3 "권장 구성" 코드블록 | upstream `dataset` extras 의 `torchcodec` 조건부 패키지 누락 — TODO-D2 입력 사양에 언급 권장 |

### Recommended 상세

#### R1 — `record` 키 이름과 lerobot upstream `dataset` 의 관계 명시 부족

**위치**: `docs/storage/09_datacollector_setup.md` §2-3 및 §2-4

**맥락**: `docs/reference/lerobot/pyproject.toml` 에 `record` 키는 존재하지 않는다. 실제 upstream 의 extras 키 이름은 `dataset`. DataCollector 의 자체 `pyproject.toml` (orin/pyproject.toml 동일 패턴 — `name = "lerobot"` 으로 lerobot curated subset 재정의) 에서 `dataset` 대신 `record` 라는 의미적으로 더 명확한 이름으로 새 키를 정의하는 의도는 기술적으로 유효하고 orin 의 `smolvla` 키 패턴과 일관된다.

그러나 §2-3 표에서는 "Extra 키: `dataset`" (upstream 키 이름) 로 기재하고, 같은 절 코드블록에서는 `record = [...]` (DataCollector 자체 pyproject.toml 의 새 키 이름) 로 정의하여, §2-4 비교표에서 "lerobot extras: `record + hardware + feetech`" 로 표현한다. 독자가 upstream `dataset` 키를 `record` 로 직접 설치하려 하면 실패한다. 코드블록 위에 "이 `record` 키는 DataCollector 자체 pyproject.toml 에 새로 정의하는 이름이며, lerobot upstream 의 `dataset` extras 에 대응한다" 는 한 줄 주석을 추가하면 혼란이 해소된다.

**영향**: TODO-D2 작성자가 잘못 이해할 경우 설치 명령을 lerobot upstream 에 직접 적용하여 `pip install lerobot[record]` 와 같은 실패 명령을 작성할 위험. (Recommended: 단순 명확성 개선. orin/pyproject.toml 패턴을 안다면 의도 추론 가능.)

#### R2 — torchcodec 조건부 패키지 누락

**위치**: `docs/storage/09_datacollector_setup.md` §2-3 권장 구성 코드블록

**맥락**: upstream `dataset` extras 에는 `torchcodec>=0.3.0,<0.11.0; sys_platform != 'win32' and ...` 조건부 패키지가 포함된다. x86_64 Linux (DataCollector) 에서 이 조건이 참이 되어 설치된다. 비디오 데이터셋 디코딩에 관여. §2-3 권장 구성에 이 패키지가 누락되어 있다.

**영향**: lerobot-record 의 비디오 관련 기능이 torchcodec 에 의존할 경우 누락 시 런타임 에러 가능. 단, TODO-D2 에서 upstream 레퍼런스를 직접 참조하여 작성하면 자연히 포함되므로 설계 문서 수준에서의 누락. (Recommended: TODO-D2 입력 사양에 "upstream dataset extras 전체 참조 — torchcodec 조건부 포함" 언급 권장.)

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. 변경 파일: `docs/storage/09_datacollector_setup.md` (신규), history 1건 — 모두 허용 영역 |
| B (자동 재시도 X 영역) | ✅ 해당 없음 | study 타입 — orin/lerobot, pyproject.toml, setup_env.sh, deploy_*.sh 미변경. 본 TODO 는 문서 신규 작성만. |
| C (사용자 동의 필수) | ✅ | 새 디렉터리 (`datacollector/`) 생성 + 외부 의존성 추가 (pyproject.toml 신규) + 환경 변경 (DataCollector venv) 모두 TODO-D2 시점 사용자 동의 확보 완료로 명시됨 (2026-05-01 awaits_user 답변 기록). 본 study 에서는 실제 디렉터리·파일 생성 없음 — 문서화만. |
| Coupled File Rules | ✅ | 본 study 에서 orin/pyproject.toml, orin/lerobot/, dgx/lerobot/ 미변경 — coupled file 의무 미발생. DataCollector lerobot 관련 `05_datacollector_lerobot_diff.md` 신규 작성 의무를 §3-5 에서 TODO-D2 시점 의무로 명시 — 올바름. |
| 옛 룰 (`docs/storage/` bash 명령 예시) | ⚠️ 경계 | `09_datacollector_setup.md` §5-1 에 SSH 서버 설치 bash 명령 예시 2줄 (`sudo apt-get install -y openssh-server`, `sudo systemctl enable ssh && sudo systemctl start ssh`) 포함. CLAUDE.md 옛 룰은 "사용자 명시 요청 없으면 `docs/storage/` 하위에 bash 명령 예시 추가 X". 단, 이 bash 예시는 운영 절차상 필수 정보이며 섹션 §5-1 SSH 설정의 일부로 자연스럽게 포함됨. TODO-D1 spec DOD 에서 "SSH 설정 기술" 을 명시하므로 사용자 명시 요청의 범주로 판단. Critical 이슈로 분류하지 않음. |

---

## Critical 이슈

없음.

---

## 사실 정확성 검증 결과 (핵심 — lerobot extras 키 대조)

`docs/reference/lerobot/pyproject.toml` 직접 대조 완료.

### 존재 확인된 키

| 키 이름 | 존재 여부 | 메모 |
|---|---|---|
| `dataset` | ✅ 존재 | upstream 정확히 `dataset`. DataCollector 에서 필요한 패키지 포함 |
| `hardware` | ✅ 존재 | pynput-dep / pyserial-dep / deepdiff-dep 참조 형태 (간접) |
| `feetech` | ✅ 존재 | `feetech-servo-sdk>=1.0.0,<2.0.0` + pyserial-dep + deepdiff-dep |
| `smolvla` | ✅ 존재 | `transformers==5.3.0` (transformers-dep), num2words, accelerate |
| `record` | ❌ 미존재 | upstream 에 없는 이름. DataCollector 자체 pyproject.toml 의 신규 정의 키 |
| `core_scripts` | ✅ 존재 | dataset + hardware + viz |
| `training` | ✅ 존재 | dataset + accelerate + wandb |
| `intelrealsense` | ✅ 존재 | pyrealsense2 조건부 |

### 판정

`09_datacollector_setup.md` §2-3 표의 extras 키 분석 (upstream 기준) 은 **정확**하다.

`record` 키는 DataCollector 자체 pyproject.toml 에 새로 정의하는 이름으로, orin/pyproject.toml 이 `smolvla` 키를 새로 정의하는 것과 동일 패턴이다. `orin/pyproject.toml` 확인 결과 `name = "lerobot"` 으로 lerobot curated subset 을 재정의하는 구조이며, DataCollector 도 동일 방식 예정. 따라서 `record` 는 설치 시 DataCollector 자신의 pyproject.toml 의 `record` extras 를 참조하므로 기술적으로 유효하다.

다만 문서 독자에게 `record` 가 upstream 키가 아닌 DataCollector 신규 정의 키임을 명시하지 않는 점 → R1 Recommended.

### 패키지 값 일치 확인

`09_datacollector_setup.md` §2-3 권장 구성의 패키지 버전 범위:
- `datasets>=4.0.0,<5.0.0` — upstream 동일 ✅
- `pandas>=2.0.0,<3.0.0` — upstream 동일 ✅
- `pyarrow>=21.0.0,<30.0.0` — upstream 동일 ✅
- `av>=15.0.0,<16.0.0` — upstream `av-dep = ["av>=15.0.0,<16.0.0"]` 와 동일 ✅
- `jsonlines>=4.0.0,<5.0.0` — upstream 동일 ✅
- `torchcodec>=0.3.0,...` — **upstream 에 있으나 누락** → R2 Recommended
- `pynput>=1.7.8,<1.9.0` — upstream pynput-dep 과 동일 ✅
- `pyserial>=3.5,<4.0` — upstream pyserial-dep 과 동일 ✅
- `deepdiff>=7.0.1,<9.0.0` — upstream deepdiff-dep 과 동일 ✅
- `feetech-servo-sdk>=1.0.0,<2.0.0` — upstream feetech 와 동일 ✅

### SSH·venv 패턴 일치

- `~/.ssh/config` 패턴: `04_devnetwork.md` §5 와 완전 일치 (Host / HostName / User / Port / IdentityFile / ServerAliveInterval / ServerAliveCountMax 6항목 동일) ✅
- venv 이름 `.hylion_collector`: `05_orin_venv_setting.md` 의 `.hylion_arm` 패턴 미러 — hidden venv + 디렉터리 안 배치 + rsync exclude 패턴 언급 모두 일치 ✅

### PyTorch 표준 wheel 반영

x86_64 Ubuntu DataCollector 에서 표준 PyPI wheel 사용 가능 사실 §2-1, §2-4, §2-5 에서 명시적으로 반영됨 ✅

---

## 07/08 패턴 미러 검증

| 항목 | 07_orin / 08_dgx 패턴 | 09_datacollector | 일치 |
|---|---|---|---|
| §0 본 문서의 위치 | 있음 | 있음 (§0 "본 문서의 위치") | ✅ |
| §1 노드 정체/디렉터리 트리 | 있음 | §1 노드 정체 | ✅ (study 특성상 재구성 허용) |
| §2 venv·의존성 | — | §2 venv·lerobot 의존성 | ✅ (study DOD 항목 반영) |
| §3 디렉터리 구조 | 있음 | §3 디렉터리 구조 | ✅ |
| §4 배치 고려사항 | §4 외부 의존성 (07) | §4 시연장 배치 고려사항 | ✅ (study 특성 반영) |
| §5 devPC 네트워크 | §5 마이그레이션 계획 (07) | §5 devPC ↔ DataCollector 네트워크 | ✅ (study DOD 항목 반영) |
| §6 향후 작업 | 있음 | 있음 | ✅ |
| §7 변경 이력 표 | 있음 | 있음 | ✅ |
| cross-reference | 07 ↔ 08 서로 형제 문서 명시 | 09 에서 07·08 형제 문서 명시 | ✅ |
| 트리 + 컴포넌트 책임 표 | 07·08 모두 포함 | §3-2 트리 + §3-3 책임 표 | ✅ |

---

## 핵심 결정 합리성 검토

| 항목 | 판단 | 근거 |
|---|---|---|
| lerobot extras subset (record+hardware+feetech) | ✅ 합리적 | lerobot-record (LeRobotDataset + HF Hub 업로드) = dataset. SO-ARM 제어 = hardware + feetech. 세 가지로 DataCollector 의 단일 책임 (데이터 수집 + teleop + SO-ARM) 충분히 커버 |
| smolvla·training 제외 | ✅ 합리적 | DataCollector 는 추론·학습 X. 책임 매트릭스 명확. |
| 옵션 B 원칙 (datacollector/lerobot/ 파일 변경 X) | ✅ 명시됨 | §3-4 에서 orin 과 동일 원칙 명시. entrypoint 만으로 비활성화 범위 제한. |
| 05_datacollector_lerobot_diff.md TODO-D2 신규 의무 | ✅ 명시됨 | §3-5 에서 coupled file 의무 및 패턴 명시. |
| run_teleoperate.sh 최종 이동 TODO-D2 명시 | ✅ 명시됨 | §6 향후 작업 및 §3-2 트리에 반영. |
| BACKLOG 02 #1 (DHCP) DataCollector 동일 카테고리 명시 | ✅ 명시됨 | §4-1 에서 기존 BACKLOG 연결 + 사용자 책임으로 명시. |

---

## SKILL_GAP / Anomaly

없음. lerobot upstream extras 직접 확인 완료. task-executor 의 "SKILL_GAP 없음" 보고에 동의.

---

## 배포 권장

READY_TO_SHIP — study 타입이므로 prod-test-runner 단계 해당 없음. D2 dispatch 게이트 통과.
