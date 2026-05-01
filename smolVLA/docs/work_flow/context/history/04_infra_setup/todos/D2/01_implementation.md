# TODO-D2 — DataCollector venv·lerobot 셋업

> 작성: 2026-05-01 | task-executor | cycle: 1

## 사전 점검 결과

- **09_datacollector_setup.md §2·§3 추출**: venv 이름 `.hylion_collector`, lerobot extras `record + hardware + feetech`, 옵션 B 원칙 (파일 변경 X), entrypoint 9개 (eval·train 제외), Python 3.12, 표준 PyPI torch wheel 확인
- **D1 code-tester R1·R2 권고 반영**: `record` extras 는 DataCollector 자체 정의 키 (upstream `dataset` 에 대응). `torchcodec>=0.3.0` 을 x86_64 Linux 조건부로 포함 (`; sys_platform == 'linux' and platform_machine == 'x86_64'`)
- **upstream 레퍼런스 확인**: `docs/reference/lerobot/pyproject.toml` 의 `dataset` extras 명세 정확히 확인. `torchcodec` 조건식은 `sys_platform != 'win32' and (sys_platform != 'linux' or (platform_machine != 'aarch64' ...))` — x86_64 Linux 환경에서 설치됨. 우리의 조건부는 이를 양수 형태로 단순화: `sys_platform == 'linux' and platform_machine == 'x86_64'`
- **orin/pyproject.toml subset 추출**: core dependencies 동일 패턴 적용. numpy 버전 범위는 DataCollector (Python 3.12) 에 맞게 `>=2.0.0,<2.3.0` (orin 의 `<2.0.0` 제약 해소 — orin 은 JP 6.0 wheel ABI 문제)

## 산출물 표

| 작업 | 카테고리 | 상태 |
|---|---|---|
| `datacollector/` 디렉터리 신규 (`scripts/ tests/ config/ data/`) | Category C 동의 | 완료 |
| `datacollector/pyproject.toml` 신규 | Category C 동의 (외부 의존성) | 완료 |
| `datacollector/scripts/setup_env.sh` 신규 | 통상 | 완료 |
| `datacollector/scripts/run_teleoperate.sh` 이관 | 자연 해소 (BACKLOG 04 #2) | 완료 |
| `datacollector/README.md` 신규 | 통상 | 완료 |
| `datacollector/tests/README.md` 신규 | 통상 | 완료 |
| `datacollector/config/README.md` 신규 | 통상 | 완료 |
| `datacollector/data/README.md` 신규 | 통상 | 완료 |
| `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 | coupled file | 완료 |
| `.gitignore` 신규 (`datacollector/data/` + venv 패턴 포함) | Category B 최소 | 완료 |
| `docs/storage/others/run_teleoperate.sh.archive` 이관 완료 표시 | 자연 해소 | 완료 |
| `docs/work_flow/specs/BACKLOG.md` 04 #2 "완료" 갱신 | 자연 해소 | 완료 |

## 핵심 결정

### record extras 정의

upstream `dataset` extras 에 대응하는 DataCollector 자체 정의 키:
- `datasets`, `pandas`, `pyarrow`, `av` — upstream 동일
- `torchcodec>=0.3.0,<0.11.0` 조건부 포함: `sys_platform == 'linux' and platform_machine == 'x86_64'`
  - x86_64 Linux (DataCollector 환경) 에서 설치됨
  - aarch64 (Orin) 에서는 설치 안 됨 (Orin pyproject 에는 미포함된 이유)
- `jsonlines` — upstream 동일

### datacollector/lerobot/ curated subset 방식

옵션 B 원칙: 파일 변경 X. `pyproject.toml entrypoint` 등록만으로 비활성화.
`datacollector/lerobot/` 실체는 `setup_env.sh §0-b` 에서 처리:
- devPC 개발 환경: upstream `docs/reference/lerobot/src/lerobot` symlink 자동 생성
- DataCollector 머신 (rsync 배포 후): `datacollector/lerobot/` 실 디렉토리가 rsync 로 전송됨

DataCollector 는 Python 3.12 이므로 orin/lerobot/ 의 Python 3.10 호환 패치 불필요.
upstream 파일 그대로 사용 가능 → orin 보다 더 순수한 옵션 B 적용.

### numpy 버전 범위

orin 은 JP 6.0 wheel ABI 문제로 `<2.0.0` 강제 고정.
DataCollector (Python 3.12, 표준 PyPI torch) 는 upstream 과 동일 `>=2.0.0,<2.3.0` 사용.

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: `05_datacollector_lerobot_diff.md` 신규 작성 ✓
- 레퍼런스 활용: `docs/reference/lerobot/pyproject.toml` 의 `dataset` extras 명세 기반으로 `record` extras 정의. `orin/pyproject.toml` + `orin/scripts/setup_env.sh` 패턴 미러.
- 옵션 B 원칙: `datacollector/lerobot/` 파일 변경 X, entrypoint 등록만 정리 ✓

## 변경 내용 요약

DataCollector 전용 환경 셋업 자산을 `smolVLA/datacollector/` 신규 디렉터리에 구성했다. orin/ 과 동일한 4-디렉터리 구조 (scripts/ tests/ config/ data/) 를 채택하고, pyproject.toml 은 orin 의 subset 으로 작성하되 DataCollector 책임 범위 (수집 전용) 에 맞게 smolvla·training extras 를 미정의했다.

setup_env.sh 는 orin 패턴을 미러하되 Jetson 특수 처리를 제거했다: cusparseLt 관련 처리 없음, LD_LIBRARY_PATH 패치 없음, 표준 PyPI torch/torchvision wheel 설치. `datacollector/lerobot/` 의 실체 구성은 setup_env.sh §0-b 에서 upstream symlink 자동 생성으로 처리하여 옵션 B 원칙을 준수했다.

BACKLOG 04 #2 의 `run_teleoperate.sh` 이관을 본 todo 에서 자연 해소했으며, `.gitignore` 신규 작성으로 venv 와 수집 데이터셋을 git 추적에서 제외했다.

## 본 사이클 자연 해소 BACKLOG

- **04 #2** (run_teleoperate.sh .archive 컨벤션) — `datacollector/scripts/run_teleoperate.sh` 로 최종 이관, BACKLOG.md 항목 "완료" 갱신

## 잔여 리스크 / SKILL_GAP

- `datacollector/lerobot/` symlink 방식은 devPC 개발 환경에서만 적용. DataCollector 머신에서는 rsync 배포 후 실 디렉토리가 존재해야 함. setup_env.sh §0-b 경고 메시지로 사용자 안내.
- `torchcodec` 조건부: upstream 의 복잡한 조건식을 단순화했음 (x86_64 Linux 양수 조건). arm64/aarch64 DataCollector 미지원 가정.
- numpy `>=2.0.0,<2.3.0` 범위는 DataCollector 환경에서 실 검증 필요 (torch 호환성).

## 검증 필요 (다음 단계)

- **code-tester**:
  - pyproject.toml valid TOML 문법 확인
  - `record + hardware + feetech` extras 키 정확성 (패키지명·버전 범위)
  - `torchcodec` 조건부 마커 문법 (`sys_platform == 'linux' and platform_machine == 'x86_64'`) 유효성
  - setup_env.sh bash 문법 검사 (`bash -n setup_env.sh`)
  - `.gitignore` 패턴 충돌 없음 확인
  - coupled file `05_datacollector_lerobot_diff.md` 갱신 누락 없음 확인
  - entrypoint 9개 모두 `datacollector/pyproject.toml [project.scripts]` 에 등록됨 확인
- **prod-test-runner (TODO-D3)**:
  - DataCollector 머신에서 `bash scripts/setup_env.sh` 실행 + `lerobot --help` 동작 확인
  - SO-ARM 연결 + `lerobot-find-port` PASS
  - 카메라 1대 연결 + `lerobot-find-cameras opencv` PASS
  - 사용자 실물 검증 필요
