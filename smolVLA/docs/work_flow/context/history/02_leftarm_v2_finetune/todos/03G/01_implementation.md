# TODO-03-G — Implementation

> 작성: 2026-05-18 | task-executor | cycle: 1

## 목표

peft 의존성을 `orin/pyproject.toml` + `orin/scripts/setup_env.sh` 에 정식 추가 (사용자 승인: 옵션 1, Category B+C 동의)

## 분기 조사 결과 — 분기 B 확정

**upstream `smolvla` extra (docs/reference/lerobot/pyproject.toml line 183):**
```toml
smolvla = ["lerobot[transformers-dep]", "num2words>=0.5.14,<0.6.0", "accelerate>=1.7.0,<2.0.0"]
```
peft 는 smolvla 에 **미포함**.

**upstream `peft-dep` (line 134):**
```toml
peft-dep = ["peft>=0.18.0,<1.0.0"]
```
별도 extra 로 분리됨. `peft` composite extra (line 201) = `[transformers-dep, peft-dep]`.

**결론 — 분기 B**: peft 가 smolvla extras 에 없음. `orin/pyproject.toml` 의 `smolvla` 섹션에 `peft>=0.18.0,<1.0.0` 명시 추가, setup_env.sh 에 검증 라인 추가.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/pyproject.toml` | M | smolvla extra 에 `peft>=0.18.0,<1.0.0` 추가 |
| `orin/scripts/setup_env.sh` | M | §6-b: peft import 검증 라인 추가 |
| `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` | M | 2026-05-18 신규 entry + 현재 차이 요약 갱신 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (참조만) ✓
- Category B 사용자 승인 받음 (2026-05-18): `orin/pyproject.toml`, `orin/scripts/setup_env.sh` 변경 OK ✓
- Coupled File Rule §1: `orin/pyproject.toml` 변경 → `setup_env.sh` 동시 갱신 ✓
- Coupled File Rule §2: `orin/pyproject.toml` 변경 → `02_orin_pyproject_diff.md` 동시 갱신 ✓
- 레퍼런스 직접 Read: `docs/reference/lerobot/pyproject.toml` line 134, 183, 201 확인
  - 인용: `peft-dep = ["peft>=0.18.0,<1.0.0"]` (line 134)
  - 인용: `smolvla = ["lerobot[transformers-dep]", "num2words>=0.5.14,<0.6.0", "accelerate>=1.7.0,<2.0.0"]` (line 183)
  - 적용: upstream peft-dep 버전 범위 그대로 채택. smolvla 에 미포함이므로 orin smolvla extra 에 직접 추가
- 최소 변경 원칙: peft 외 다른 의존성 미변경. torch/torchvision/numpy 는 setup_env.sh 에서만 관리 (불변) ✓

## 변경 내용 요약

`leftarm_v2_inference.py` (TODO-03-F) 가 LoRA adapter checkpoint 를 로드하기 위해 `peft` 라이브러리를 임포트한다. Orin SSH 확인 결과 peft 미설치 상태였으며, upstream lerobot 의 `smolvla` extra 에도 peft 가 포함되지 않아 별도 추가가 필요한 분기 B 상황이었다.

upstream `peft-dep = ["peft>=0.18.0,<1.0.0"]` 버전 범위를 그대로 채택하여 `orin/pyproject.toml` 의 `smolvla` 섹션에 추가했다. `setup_env.sh` 에는 §6-b 검증 라인을 추가하여 재실행 시 peft import 가 정상인지 자동 확인되도록 했다. 실 venv 재 install (`pip install -e orin/[smolvla,hardware,feetech]`) 은 prod-test-runner cycle 3 에서 SSH 로 진행한다.

## code-tester 입장에서 검증 권장 사항

- **pyproject.toml 문법**: `python -c "import tomllib; tomllib.loads(open('orin/pyproject.toml').read())"` 또는 `pip install --dry-run -e orin/[smolvla]`
- **setup_env.sh 구문**: `bash -n orin/scripts/setup_env.sh`
- **02_orin_pyproject_diff.md 정합성**:
  - 신규 entry 날짜·이유·before/after diff 포함 여부
  - 현재 차이 요약 smolvla 행 갱신 여부
- **Coupled Rule 충족**:
  - setup_env.sh §6-b 검증 라인 존재 여부
  - 02_orin_pyproject_diff.md 신규 entry 존재 여부
- **DOD 항목**:
  - peft 버전 범위가 upstream peft-dep (>=0.18.0,<1.0.0) 와 일치하는지
  - aarch64/cp310 환경 적합성 (pure-Python 패키지, 플랫폼 무관)

## 잔여 리스크

| 리스크 | 수준 | 완화 |
|---|---|---|
| aarch64 wheel 가용성 | 낮음 | peft 는 pure-Python 패키지 — 플랫폼 무관 wheel (any) 제공됨 |
| transitive deps 충돌 | 낮음 | peft 의 주 의존성 (tqdm, huggingface-hub, transformers) 이미 설치됨 |
| install 시간 | 낮음 | peft 경량 (~수 MB). 전체 venv 재설치 시 lerobot 설치 포함 수 분 예상 |
| 디스크 영향 | 낮음 | 측정 필요 (prod-test-runner cycle 3) |
| peft 버전 >=0.18.0 API 호환성 | 중간 | `leftarm_v2_inference.py` 가 peft 0.10+/0.18+ API 사용하는지 확인 권장 |
