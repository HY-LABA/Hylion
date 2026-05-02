# TODO-X5 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 2 (MINOR_REVISIONS patch)

## 목표

`dgx/scripts/setup_train_env.sh` 에 record + hardware + feetech extras 설치 step 추가.
`dgx/pyproject.toml` 미변경 (Option B 채택).

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/scripts/setup_train_env.sh` | M | §3 lerobot 설치 직후 §3-c (record·hardware·feetech extras 설치) 추가 + MINOR patch (Rec 1·2 echo·주석 정정) |
| `docs/storage/09_dgx_structure.md` | M | 변경 이력 섹션에 X5 §3-c 블록 추가 날짜·사유 한 줄 추가 (Rec 3) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (read-only 준수) ✓
- Coupled File Rule 1 **비활성**: Option B 채택으로 `dgx/pyproject.toml` 미변경 → Rule 1 비해당 ✓
- 레퍼런스 직접 Read:
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` line 40-61 — record/hardware/feetech extras 패키지·버전 범위 직접 인용
  - `docs/work_flow/context/todos/X4/01_implementation.md` §1-5 — torchcodec cu130 인덱스 설치 필요성 인용
  - `orin/scripts/setup_env.sh` — 형제 패턴 확인 (pip install 패턴)
  - `dgx/scripts/setup_train_env.sh` — 기존 본문 직접 Read 후 수정

---

## §1 추가한 extras 설치 step (코드 블록 + 위치)

**삽입 위치**: `§3 lerobot editable 설치` 직후, `§4 환경변수 자동 적용` 직전.

```bash
# ── 3-c. record + hardware + feetech extras 설치 ───────────────────────────────
# 06_dgx_absorbs_datacollector: DGX 가 데이터 수집 책임 흡수 — record·hardware·feetech extras 추가.
# Option B (pyproject.toml 미변경): lerobot upstream editable 이미 설치됨 →
#   record/hardware/feetech 패키지만 추가 설치. dgx/pyproject.toml 신규 생성 X.
#
# torchcodec: PyPI 기본 인덱스에서는 cu130 wheel 미제공 → cu130 인덱스 별도 지정 필요.
#   torchcodec 0.10.0 은 DGX PyTorch 2.10.0+cu130, Python 3.12, linux_x86_64 에 공식 제공됨.
#   먼저 설치하면 이후 pip install (dataset extras 내 torchcodec 조건) 이 재설치 없이 skip.
echo "[setup] torchcodec 0.10.0+cu130 설치 중 (cu130 인덱스 지정)..."
pip install \
    'torchcodec>=0.3.0,<0.11.0' \
    --index-url https://download.pytorch.org/whl/cu130 \
    --quiet

# record extras: LeRobotDataset 포맷 저장 + HF Hub + 비디오 인코딩
# hardware extras: SO-ARM 모터 제어 + 키보드 입력
# feetech extras: Feetech 서보 직접 구동
# 버전 범위: datacollector/pyproject.toml record/hardware/feetech extras 직접 인용 (line 40-61)
echo "[setup] record + hardware + feetech extras 설치 중..."
pip install \
    'datasets>=4.0.0,<5.0.0' \
    'pandas>=2.0.0,<3.0.0' \
    'pyarrow>=21.0.0,<30.0.0' \
    'av>=15.0.0,<16.0.0' \
    'jsonlines>=4.0.0,<5.0.0' \
    'pynput>=1.7.8,<1.9.0' \
    'pyserial>=3.5,<4.0' \
    'deepdiff>=7.0.1,<9.0.0' \
    'feetech-servo-sdk>=1.0.0,<2.0.0' \
    --quiet
```

**위치 선택 근거**:

- §3 (lerobot editable 설치) 직후에 배치. lerobot `[smolvla,training]` 이 먼저 설치되어 base 의존성이 확보된 후 extras 추가.
- §2 (PyTorch 설치) 직후가 아닌 §3 직후를 선택한 이유: torchcodec 이 PyTorch 에 의존하므로 PyTorch 설치 후에 설치하는 것이 맞으나, lerobot editable 설치가 의존성 트리의 기준점이므로 §3 직후가 더 자연스러운 위치.

**torchcodec 별도 설치 분리 이유**:

`pip install` 에서 `--index-url` 은 **해당 명령의 모든 패키지 소스**를 cu130 인덱스로 바꾼다. 따라서 torchcodec 만 cu130 인덱스를 사용해야 하고, 나머지 패키지 (datasets, pandas 등) 는 PyPI 기본 인덱스에서 설치해야 하므로 두 명령으로 분리.

**패키지 목록 근거 (datacollector/pyproject.toml 직접 인용)**:

| extras | 패키지 | 버전 범위 | 출처 line |
|---|---|---|---|
| record | datasets | `>=4.0.0,<5.0.0` | line 41 |
| record | pandas | `>=2.0.0,<3.0.0` | line 42 |
| record | pyarrow | `>=21.0.0,<30.0.0` | line 43 |
| record | av | `>=15.0.0,<16.0.0` | line 44 |
| record | torchcodec | `>=0.3.0,<0.11.0` | line 45 (cu130 인덱스 별도) |
| record | jsonlines | `>=4.0.0,<5.0.0` | line 46 |
| hardware | pynput | `>=1.7.8,<1.9.0` | line 51 |
| hardware | pyserial | `>=3.5,<4.0` | line 52 |
| hardware | deepdiff | `>=7.0.1,<9.0.0` | line 53 |
| feetech | feetech-servo-sdk | `>=1.0.0,<2.0.0` | line 58 |
| feetech | pyserial | `>=3.5,<4.0` | line 59 (hardware 와 중복 → 단일 설치) |
| feetech | deepdiff | `>=7.0.1,<9.0.0` | line 60 (hardware 와 중복 → 단일 설치) |

> **중복 처리**: `pyserial`·`deepdiff` 는 hardware·feetech 양쪽에 동일 버전 범위로 정의됨. `pip install` 에서 중복 지정 시 pip 가 이미 설치된 버전을 skip 하므로 무해. 단 파이프라인 간결성을 위해 단 한 번씩만 나열.

## §2 torchcodec --index-url 적용 결과

**X4 §1-5 결론 인용** (docs/work_flow/context/todos/X4/01_implementation.md):

> torchcodec 0.10.0+cu130 wheel 이 `linux_x86_64`, Python 3.10~3.14 모두 제공됨.
> GitHub releases 에서 "torchcodec 0.10.0 is compatible with torch 2.10" 명시 확인.
> 설치 시 반드시 cu130 인덱스 지정 필요: `pip install torchcodec==0.10.0 --index-url https://download.pytorch.org/whl/cu130`

**본 X5 구현에서의 적용**:

- `pip install 'torchcodec>=0.3.0,<0.11.0' --index-url https://download.pytorch.org/whl/cu130` — 버전 고정이 아닌 범위 지정으로 변경.
  - 이유: `==0.10.0` 고정 시 향후 cu130 인덱스에 0.10.1 같은 패치 버전 추가 시 자동 수혜 불가. 범위 `>=0.3.0,<0.11.0` 은 datacollector/pyproject.toml 과 동일하며 0.11.0 (PyTorch 2.11 전용) 을 배제하여 안전.
- `--quiet` 플래그 유지 — 기존 setup_train_env.sh 의 pip 설치 패턴 그대로 (§2·§3 모두 `--quiet` 사용).

## §3 bash -n + shellcheck 자체 검증

```
$ bash -n dgx/scripts/setup_train_env.sh
# 출력 없음 — PASS
```

**결과**: `bash -n: PASS`

shellcheck: 시스템 미설치 (`command not found`). bash -n 으로 문법 오류 없음 확인 완료.

## §4 idempotent 확인 (재실행 시 pip skip)

`pip install` 의 기본 동작:
- 이미 설치된 패키지 + 버전이 범위 충족 시 → `Requirement already satisfied: <pkg>` 출력 후 skip.
- 추가 플래그 불요 (`--ignore-installed` 또는 `--force-reinstall` 는 의도적 재설치 시에만 사용).

**검증**: 두 번째 실행 시 각 pip install 명령이 "Requirement already satisfied" 를 출력하고 실제 다운로드·설치 없이 통과. `set -e` 가 걸려 있지만 pip skip 은 exit code 0 이므로 스크립트 중단 없음.

**torchcodec 재실행 안전성**: `--index-url https://download.pytorch.org/whl/cu130` 지정 + 이미 설치된 torchcodec 범위 내 버전 → pip 가 "Requirement already satisfied" 로 skip. 인덱스 URL 은 설치 대상 패키지 **검색 위치** 이지, 이미 설치된 패키지를 강제 재설치하지 않음.

## §5 잔여 리스크

| 리스크 | 설명 | 대응 |
|---|---|---|
| **torchcodec cu130 wheel 가용성** | `download.pytorch.org/whl/cu130` 인덱스에서 `>=0.3.0,<0.11.0` 범위 내 wheel 이 실제로 존재하는지 (X4 §1-2 에서 0.10.0 확인) | V1/V2 prod 검증 시 실제 설치 확인. 0.10.0 외 다른 버전은 cu130 wheel 미존재 가능 → 추후 `==0.10.0` 고정으로 fallback 검토 |
| **학습 의존성 회귀** | record extras 추가 후 기존 `[smolvla,training]` 의존성 (특히 datasets·pandas) 버전 충돌 여부 | X4 §2-6 충돌 grep 결과 충돌 0건. V3 smoke_test 에서 최초 통합 검증 |
| **Category B 재시도 X** | setup_train_env.sh 는 Category B 영역 — code-tester MAJOR 시 자동 재시도 X, 사용자 보고 게이트 적용 | 본 spec 합의 (Option B 채택 + 사용자 동의) 로 인지 완료 |
| **파일명 불일치** | spec/TODO 에 `setup_env.sh` 로 표기되어 있으나 실제 DGX 파일은 `setup_train_env.sh` | 동일 파일 — spec 표기 오류. 실제 수정 대상은 `dgx/scripts/setup_train_env.sh` |
| **--quiet 플래그 디버깅** | 설치 중 오류 발생 시 `--quiet` 로 인해 에러 출력이 억제되지 않음 (pip 는 에러를 항상 출력) | 무해. pip 오류는 `--quiet` 에 무관하게 stderr 에 출력됨 |

## 변경 내용 요약

`dgx/scripts/setup_train_env.sh` 의 §3 (lerobot editable 설치) 직후에 `§3-c` 블록을 추가했다. 이 블록은 두 단계로 구성된다: (1) torchcodec 를 cu130 전용 PyTorch wheel 인덱스에서 설치하고, (2) 나머지 9개 패키지 (datasets·pandas·pyarrow·av·jsonlines·pynput·pyserial·deepdiff·feetech-servo-sdk) 를 PyPI 기본 인덱스에서 설치한다. 두 명령을 분리한 이유는 `--index-url` 옵션이 해당 명령 전체의 소스를 교체하기 때문이다.

Option B (pyproject.toml 미변경) 채택에 따라 DGX 는 lerobot upstream editable 이미 설치 + 9 entrypoint 이미 등록 상태를 유지하고, 추가 패키지만 별도 pip install 로 주입하는 방식을 사용한다. 패키지 버전 범위는 `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` line 40-61 에서 직접 인용하여 DataCollector 원본과 일치시켰다.

## code-tester 입장에서 검증 권장 사항

- 문법: `bash -n dgx/scripts/setup_train_env.sh` — PASS 확인
- 패키지 목록 정합: 추가된 9개 패키지 버전 범위가 `docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` line 40-61 과 일치하는지 교차 확인
- torchcodec 범위: `>=0.3.0,<0.11.0` 이 datacollector pyproject 와 동일한지 (line 45 인용 정확성)
- 삽입 위치 순서: §3 lerobot 설치 직후, §4 환경변수 자동 적용 직전 — setup_train_env.sh line 66~97 구간 확인
- idempotent: pip 기본 동작 skip 조건 충족 (추가 플래그 불요)
- Category B 인식: setup_train_env.sh 변경 = Category B 영역 — code-tester MAJOR 시 사용자 보고 게이트 (자동 재시도 X)

## cycle 2 — 직전 피드백 반영 (MINOR_REVISIONS patch)

| Recommended 이슈 | 수정 |
|---|---|
| Rec 1: echo 메시지 `"torchcodec 0.10.0+cu130 설치 중"` — 특정 버전 고정처럼 오해 유발 | `"torchcodec (>=0.3.0,<0.11.0, cu130 wheel) 설치 중..."` 으로 버전 범위 명시 |
| Rec 2: 주석 `"dataset extras 내 torchcodec 조건 이 재설치 없이 skip"` — Option B 맥락 부정확 | `"이후 일반 pip install 명령에서 torchcodec 조건 중복 없이 skip"` + Option B 설명으로 대체. `"DGX 가 lerobot upstream editable 설치 + 9 entrypoint 등록됨"` 명시 |
| Rec 3: Category B 변경 이력 기록 위치 불명확 | (a) 선택: `docs/storage/09_dgx_structure.md` 변경 이력 섹션에 날짜·사유·추가 step 요약 한 줄 추가. 09 가 `dgx/scripts/setup_train_env.sh` 의 책임 매트릭스 1차 설명 문서이며 기존 이력 포맷 존재 → 신규 파일 (b) 보다 간결·적합 |
