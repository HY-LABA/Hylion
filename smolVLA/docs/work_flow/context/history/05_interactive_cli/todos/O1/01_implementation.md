# TODO-O1 — Implementation

> 작성: 2026-05-01 | task-executor | cycle: 1

## 목표

orin 측 interactive_cli flow 3~ 단계 (추론 책임) 를 분석하여 후보 옵션을 도출하고
사용자 합의를 위한 awaits_user-B 발송 명세를 작성한다.

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/13_orin_cli_flow.md` | 신규 | orin flow 2~5 분석 + 후보 A·B·C + ckpt 선택 메커니즘 + hil_inference 호출 구조 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `docs/storage/` 신규 파일만 (Category 미해당).
- Coupled File Rule: orin/lerobot/ 및 pyproject.toml 미변경 — Coupled File 갱신 불필요.
- 레퍼런스 직접 Read:
  - `orin/inference/hil_inference.py` 전체 Read + `--gate-json` argparse (line 235~245), `load_gate_config()` (line 80~119), `apply_gate_config()` (line 122~177) 인용
  - `docs/storage/08_orin_structure.md` — orin/checkpoints/ 구조 + 마일스톤별 책임 매트릭스 인용
  - `orin/tests/check_hardware.sh` (line 41~49 경로 상수) 인용
  - `scripts/sync_ckpt_dgx_to_datacollector.sh` — checkpoints/<run>/<step>/pretrained_model 경로 패턴 인용
  - `docs/work_flow/context/history/04_infra_setup/verification_queue.md` §G2 — first-time/resume 환경 조건 확인
  - `docs/storage/12_interactive_cli_framework.md` §5 env_check.py 참조 패턴 인용

---

## 변경 내용 요약

`orin/inference/hil_inference.py` 전체와 관련 레퍼런스 파일들을 직접 Read 하여
orin interactive_cli 의 flow 3~ 단계 후보를 3개 도출했다.

핵심 발견: `--gate-json` 인자 (line 235~245) 가 `orin/config/ports.json` 과
`cameras.json` 을 자동으로 로드하여 `--follower-port`, `--cameras`, `--flip-cameras`
를 채워 준다. interactive_cli 는 `--gate-json orin/config/` 만 자동 전달하면 사용자가
포트·카메라 인덱스를 직접 입력할 필요가 없다. 단 현재 hil_inference.py 는 MODEL_ID 가
line 48 에 `"lerobot/smolvla_base"` 로 하드코드되어 있어, 로컬 ckpt 또는 사용자 HF
repo_id 를 받으려면 O2 에서 `--ckpt-path` / `--model-id` 인자 추가가 필요하다.
`orin/inference/hil_inference.py` 는 `orin/inference/` 하위로 Category B 비해당 — 일반 코드 수정.

flow 3~ 후보 3개를 `docs/storage/13_orin_cli_flow.md` §2 에 정리:

- 후보 A (3단계 순차): ckpt 선택 → hil_inference 실행 → 결과 보고. 가장 직관적.
- 후보 B (2단계 통합): ckpt 선택 + 옵션 → hil_inference 실행. 최소 단계.
- 후보 C (4단계 재실행): 추가 옵션 설정 + 재실행 루프. 반복 실험 편의.

ckpt 선택 소스 4가지 (§3), hil_inference.py 호출 구조의 `--gate-json` 자동 채움 패턴
(§4), 시연 데모 모드 포함 여부 (§5) 를 각 절에서 분석했다.

---

## code-tester 입장에서 검증 권장 사항

- 레퍼런스 인용 정합성: `01_implementation.md` 의 인용 라인 번호가 실제 `hil_inference.py` 라인과 일치하는지 확인
  - `--gate-json` argparse: line 235~245 (hil_inference.py)
  - `load_gate_config()`: line 80~119
  - `apply_gate_config()`: line 122~177
  - `MODEL_ID` 하드코드: line 48
- docs/storage/13_orin_cli_flow.md 의 §4 호출 구조 예시가 hil_inference.py 실제 CLI 인터페이스와 일치하는지 확인
  - dry-run 시 `--output-json` 필수 (hil_inference.py line 257~259)
  - `--gate-json` 미지정 + `--follower-port` 미지정 시 parser.error() 발생 (line 253~255)
- Category 분류 확인: O2 에서 hil_inference.py 수정 예정 (`orin/inference/` 하위 — Category B 비해당, 일반 코드 수정)

---

## awaits_user-B 발송 내용

orin interactive_cli 의 flow 3~ 단계 구체 책임을 선택해 주세요.

`orin/inference/hil_inference.py` 전체 Read + `docs/storage/08_orin_structure.md` 분석 결과 다음 후보를 도출했습니다:

### (A) 3단계 순차

```
flow 3. ckpt 선택
         - (1) HF Hub repo_id 입력 (기본: lerobot/smolvla_base)
         - (2) 로컬 ckpt 경로 입력 (orin/checkpoints/ 자동 탐색 제안)
         - (3) 기본값 smolvla_base 사용 (입력 없이 Enter)
flow 4. hil_inference.py 실행
         - --gate-json orin/config/ 자동 전달 (follower-port·cameras·flip 자동 채움)
         - dry-run 또는 live 선택
         - Ctrl+C 또는 max-steps 도달 시 종료
flow 5. 결과 보고
         - 실행 step 수 / 모드 / action JSON 경로 출력
```

### (B) 2단계 통합

```
flow 3. ckpt 선택 + 실행 옵션 결정 (1화면)
         - ckpt 소스 선택 + dry-run/live + max-steps
         - "시작하겠습니까? [Y/n]" 확인
flow 4. hil_inference.py 실행
         - stdout 그대로 출력 (별도 데모 단계 없음)
         - 완료 후 종료
```

### (C) 4단계 재실행 루프

```
flow 3. ckpt 선택
flow 4. 실행 옵션 설정 (dry-run/live/max-steps/n-action-steps)
flow 5. hil_inference.py 실행 (step 카운터 모니터링)
flow 6. 결과 요약 + 재실행 여부 질문
         ("동일 ckpt 재실행 / 다른 ckpt 선택 / 종료")
```

---

**추가 결정 사항** (A/B/C 공통):

- `orin/inference/hil_inference.py` 에 `--ckpt-path` 인자를 추가해야 로컬 ckpt 로드가 가능합니다.
  이 파일은 `orin/inference/` 하위로 Category B 비해당 (일반 코드 수정) — O2 에서 사용자 동의 없이 자동 처리됩니다.
- 시연 데모 모드 포함 여부:
  - 포함 (A·C): "로봇이 움직이고 있습니다" + Ctrl+C 종료 안내
  - 미포함 (B): hil_inference stdout 로그 그대로

**영향**: O2 의 `flows/inference.py` 구조 (단계 수 / ckpt 선택 UI / `--gate-json` 자동 채움 / 시연 데모 출력 포함 여부) 결정.

---

## 다음 단계 권고 (O2 task 입력 명세)

O2 dispatch 는 사용자의 후보 선택 확정 후 가능합니다.
사용자 답 후 O2 가 받을 입력:

1. **선택된 flow 구조** — 후보 A/B/C 중 하나 (또는 변형)
2. **ckpt 선택 소스 조합** — 지원할 소스 조합:
   - (1) HF Hub repo_id 입력 여부
   - (2) 로컬 ckpt 경로 입력 여부
   - (3) orin/checkpoints/ 자동 탐색 여부
   - (4) 기본값 smolvla_base 고정 여부
3. **시연 데모 모드 포함 여부** — 포함 (A·C) 또는 미포함 (B)

O2 구현 대상:
- `orin/interactive_cli/flows/inference.py` (신규) — 위 결정 기반
- `orin/inference/hil_inference.py` — `--ckpt-path` 인자 추가 (일반 코드 수정, Category B 비해당)
  (`orin/lerobot/` 하위 아님 → `03_orin_lerobot_diff.md` 갱신 불필요)

---

## 잔여 리스크

- `orin/inference/hil_inference.py` 의 `--ckpt-path` 추가는 일반 코드 수정 (Category B 비해당) — O2 에서 사용자 동의 없이 자동 처리 가능
- 04 G2 verification_queue §1번 (check_hardware.sh first-time + ports.json·cameras.json 실 값 캐시) 미완료 시 flow 2 가 실패함 — O3 prod 검증 전 G2 검증 완료 선행 필요
- ckpt 선택 단계에서 `orin/checkpoints/` 가 비어 있으면 (04 T2 전송 미완료) 소스 (2)·(4) 는 선택 불가 — flow 3 에서 graceful 안내 필요 (O2 구현 시 처리)
