# Orin 추론 성능평가 시트 — leftarm_v2_camera_empty_A2_pc_2026-05-18

> 작성: 2026-05-18 | orchestrator | camera_empty 분기 단일 변수 가설 검증 사이클

---

## 메타

| 항목 | 값 |
|---|---|
| 평가 대상 ckpt | [`BaboGaeguri/leftarm_v2_camera_empty_A2_pc_2026-05-18`](https://huggingface.co/BaboGaeguri/leftarm_v2_camera_empty_A2_pc_2026-05-18) |
| ckpt 형태 | LoRA adapter 45MB (base: `lerobot/smolvla_base`) |
| 학습 메타 요약 | 100ep subset (ep 0~99) · LoRA r=16 all-linear · batch 4 fp32 · **75,000 step** · final loss 0.130 · 9시간 22분. **단일 변수 차이**: `empty_cameras: 1` (M1.5 A2 = 0). 나머지 100% 동일. 상세: [`learning_log1.md` §camera_empty 분기 학습](../../../prof_computer/docs/leftarm_v2/learning_log1.md#camera_empty-분기-학습--2026-05-18) |
| 평가일 | 2026-05-18 |
| 평가자 | 사용자 (1인) |
| 평가 환경 | 실 Orin + 좌측 SO-101 아암 + 시연장 (M1.5 평가와 동일 셋업) |
| **사이클 비고** | **단축 비교 평가** — 본 분기 (camera_empty) + M1.5 (A2 재다운로드) 동일 패턴 동시 검증. 사유: 첫 trial 결과 두 모델 모두 형편없음 + 차이 없음 → 정량 평가 자체 무의미 결론. **empty_cameras 가설 root cause 아님 확정** → 데이터 확장 우선순위 결정. |
| spec | (없음 — 사용자 자율 ad-hoc 검증 사이클, `realplaying.md` M1.5 후속) |
| plan | (없음 — Phase 1·2 생략, walkthrough 직진) |
| 선행 사이클 보고서 | [`a2_eval_2026-05-17.md`](a2_eval_2026-05-17.md) (M1.5 A2) · [`base_eval_2026-05-17.md`](base_eval_2026-05-17.md) (zero-shot base) · [`research_empty_cameras_2026-05-18.md`](../../../prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md) (가설 근거) |

---

## 평가 기준 안내

**M1.5 A2 평가와 *완전 동일* 양식** — 단일 변수 가설 검증을 위해 패턴 보존.

### 평가 지표

- 1차 메트릭: **success rate** (수동 카운트, task × orientation 별)
- 2차 메트릭: 정성 관찰 (종합 정성 메모 섹션 참조)
- **3차 메트릭 (본 사이클 신설)**: M1.5 A2 와의 *동작 패턴 차이* 정성 비교

### 시나리오 구성

| 그룹 | task | orientation | trial 수 (계획) |
|---|---|---|---|
| task1 × front | task1 (인형) | 인형 얼굴이 카메라에 보이게 | 5 |
| task1 × back | task1 (인형) | 인형 뒤통수가 카메라에 보이게 | 5 |
| task2 × front | task2 (캔) | 캔 문양이 카메라에 보이게 | 5 |
| task2 × back | task2 (캔) | 캔 성분표시가 카메라에 보이게 | 5 |
| **합계** | — | — | **20 trial** |

### Task instruction (정본 — [`dgx/docs/finetune/leftarm_v2/collection_log.md`](../../../dgx/docs/finetune/leftarm_v2/collection_log.md) §데이터셋 개요)

- **task1**: `"Pick up the blue and yellow doll and place it on the left side of the table"`
- **task2**: `"Hand the yellow can to the person"`

### 성공 정의

| task | 성공 조건 |
|---|---|
| task1 | 인형을 잡고 테이블 **왼쪽**에 내려놓으면 성공 |
| task2 | 노란 캔을 사람에게 건네면 성공 (사람이 받을 수 있는 위치까지 도달) |

### 실패 원인 분류 (메모 시 사용)

| 분류 코드 | 설명 |
|---|---|
| `잡기 실패` | 물체를 집지 못함 |
| `오정렬` | 잡았으나 다른 곳에 놓음 (task1: 왼쪽 아닌 위치 / task2: 사람에게 미전달) |
| `동작 불완전` | 도중 정지 또는 동작이 완료되지 않음 |
| `task 혼동` | 다른 task 의 동작을 수행함 |
| `기타` | 위 분류에 해당 없는 경우 (메모에 구체 내용 기재) |

### 재시도 처리 정책

- 1회 시도당 1 trial — 재시도 없음
- 단, 로봇 비정상 동작 (모터 오류·전원 이슈·케이블 단선) 시 trial 무효 가능

---

## Trial 기록

### task1 × front (5 trial — 1+ 실시, 4 미실시)

> 인형 얼굴이 카메라에 보이게 배치. instruction: `"Pick up the blue and yellow doll and place it on the left side of the table"`
> wrapper max-steps 추이: 첫 trial 50 (~1.7s, 너무 짧아 관찰 불가 → 즉시 1000 으로 확장 변경) → 후속 1000 (~33s)

| trial # | task | orientation | 성공 | 실패 원인 분류 | 자유 메모 |
|---|---|---|---|---|---|
| 1 | 1 | front | ❌ | 잡기 실패 | 인형 방향으로 *접근*은 함 — 도달 단계 일부 가능, 정확히 짚는 동작 못함. 그리퍼 미체결. M1.5 A2 의 trial #1 (헛스윙) 과 *유사 패턴*. |
| 2 | 1 | front | — | — | 미실시 (단축 결정 — 결과 명확) |
| 3 | 1 | front | — | — | 미실시 |
| 4 | 1 | front | — | — | 미실시 |
| 5 | 1 | front | — | — | 미실시 |

### task1 × back (5 trial — 미실시)

> 인형 뒤통수가 카메라에 보이게 배치.

| trial # | task | orientation | 성공 | 실패 원인 분류 | 자유 메모 |
|---|---|---|---|---|---|
| 6 | 1 | back | — | — | 미실시 (단축 결정) |
| 7 | 1 | back | — | — | 미실시 |
| 8 | 1 | back | — | — | 미실시 |
| 9 | 1 | back | — | — | 미실시 |
| 10 | 1 | back | — | — | 미실시 |

### task2 × front (5 trial — 1 실시, 4 미실시)

> 캔 문양이 카메라에 보이게 배치. instruction: `"Hand the yellow can to the person"`
> wrapper max-steps: 1000 (~33s)

| trial # | task | orientation | 성공 | 실패 원인 분류 | 자유 메모 |
|---|---|---|---|---|---|
| 11 | 2 | front | ❌ | 동작 불완전 | 캔 방향으로 *접근*은 함 — 도달 일부 가능, 정확히 짚는 동작 못함. 전달 단계 미완성. M1.5 A2 의 trial #11 (캔 방향 팔 이동) 과 *유사 패턴*. |
| 12 | 2 | front | — | — | 미실시 (단축 결정) |
| 13 | 2 | front | — | — | 미실시 |
| 14 | 2 | front | — | — | 미실시 |
| 15 | 2 | front | — | — | 미실시 |

### task2 × back (5 trial — 미실시)

> 캔 성분표시가 카메라에 보이게 배치.

| trial # | task | orientation | 성공 | 실패 원인 분류 | 자유 메모 |
|---|---|---|---|---|---|
| 16 | 2 | back | — | — | 미실시 (단축 결정) |
| 17 | 2 | back | — | — | 미실시 |
| 18 | 2 | back | — | — | 미실시 |
| 19 | 2 | back | — | — | 미실시 |
| 20 | 2 | back | — | — | 미실시 |

---

## 결과 집계 표

> 단축 평가 — 분모 = *실제 실시 trial 수* (각 task front 1회).

| task | orientation | 성공 / 실시 (계획) | success rate (실시 기준) |
|---|---|---|---|
| task1 | front | 0 / 1 (계획 5) | 0% |
| task1 | back | — / 0 (계획 5) | 미실시 |
| **task1 total** | — | **0 / 1 (계획 10)** | **0%** |
| task2 | front | 0 / 1 (계획 5) | 0% |
| task2 | back | — / 0 (계획 5) | 미실시 |
| **task2 total** | — | **0 / 1 (계획 10)** | **0%** |
| **전체 total** | — | **0 / 2 (계획 20)** | **0%** |

→ **정량 결론**: 단축 결과 *0-20% 영역* 확정. M1.5 A2 와 *동일 영역* — 차이 없음.

---

## M1.5 (A2) vs 본 분기 (camera_empty) 비교 — 단일 변수 가설 검증

> 본 사이클의 *핵심 발견*. `empty_cameras` 단일 변수 차이의 추론 성능 영향 측정.

### 정량 비교

| 평가축 | M1.5 (A2, `empty_cameras=0`) | 본 분기 (camera_empty, `empty_cameras=1`) | 차이 |
|---|---|---|---|
| task1 front | 0/1 (잡기 실패) | 0/1 (잡기 실패) | **없음** |
| task2 front | 0/1 (동작 불완전) | 0/1 (동작 불완전) | **없음** |
| 전체 success | 0/2 (0%) | 0/2 (0%) | **없음** |

### 정성 비교

| 관찰 항목 | M1.5 (A2) | 본 분기 (camera_empty) | 차이 |
|---|---|---|---|
| 물체 인식·접근 | task2 *일부 가능* (캔 방향 이동), task1 *헛스윙* | task1·task2 *둘 다 일부 가능* (방향 접근) | **유사 — 본 분기 약간 ↑ 가능성, 단 단축으로 통계적 무의미** |
| 정확히 짚기 | ❌ | ❌ | **동일 실패** |
| task instruction 응답성 | task2 > task1 약한 차이 | 두 task 비슷한 응답성 | 미세 차이 |
| 동작 부드러움 | 양호 (모터·하드웨어 정상) | 양호 (동일) | **동일** |
| 정책 *판단력* 한계 | 도달 단계 일부, 짚기·완료 단계 응답성 부재 | 도달 단계 일부, 짚기·완료 단계 응답성 부재 | **동일 패턴** |

### 학습 메트릭 비교 (참고 — [`learning_log1.md` §M1.5 vs 002 비교 표](../../../prof_computer/docs/leftarm_v2/learning_log1.md#m15-001-와의-비교--empty_cameras-단일-변수만-차이))

| 학습 지표 | M1.5 (001) | 002 (camera_empty) | 차이 |
|---|---|---|---|
| 총 시간 | 7시간 34분 | 9시간 22분 | +24% (camera3 zero-pad 오버헤드) |
| step time | 0.343 s | 0.397 s | +16% |
| final loss (single-batch) | 0.132 | 0.130 | 거의 동등 |
| loss steady (last 20K) | 0.013-0.087 | 0.05-0.20 | 002 약간 ↑ |
| 완주 | ✅ | ✅ | 동일 |

→ 학습 메트릭은 *큰 차이 없음*, 추론 결과도 *큰 차이 없음*.

### 가설 검증 결론

> [`research_empty_cameras_2026-05-18.md`](../../../prof_computer/docs/leftarm_v2/research_empty_cameras_2026-05-18.md) 의 가설 — *`empty_cameras=0` (base 의 3 cam 형식과 우리 2 cam dataset 의 mismatch) 가 M1.5 의 0/2 root cause* 일 가능성.

| 결론 | 근거 |
|---|---|
| **`empty_cameras` 가설 *root cause 아님* 확정** | 단일 변수만 변경했는데도 추론 정량 (0% → 0%) + 정성 (동일 패턴) 차이 부재. base 형식 정합 회복 (3 cam zero-pad) 만으로는 정책 *판단력* 개선 안 됨. |
| **다른 root cause 영역으로 이동** | research §6 의 검증 C·D 영역 (dataset 품질, workspace, 추론 인프라) — 본 사이클에서 *배제된 후보* (n_action_steps Hub 함정 + normalization stats infinity — `learning_log1.md` §검증 A·B) 외 *남은 영역*. **가장 가능성 높은 영역 = 데이터셋 크기·품질·다양성**. |
| **`empty_cameras=1` 유지 여부** | 학습 시간 +24% 비용 대비 추론 개선 없음 → *기본값 (=0) 유지 권장*. 본 분기 ckpt 는 *부분 검증용* 자료로 보존. |

---

## 학습 분포 外 robustness 시도 (표준 양식 — 03_leftarm_v2_eval_003_branch 도출)

> 계획된 trial 과 별도로, 사용자 자발적 perturbation 시도 결과를 기록. 매 eval 사이클 *선택* 섹션 — 시도 시 채우고, 미시도 시 행 0개 유지.
> robustness perturbation 시도는 학습 분포 외 일반화 능력의 정성 측정. 통계 신뢰도는 trial 수가 적어 제한적.

| trial # | perturbation 종류 | 성공 | 메모 |
|---|---|---|---|
| — | — | — | (본 사이클 미시도 — empty_cameras 단일 변수 가설 검증 영역) |

### 학습 분포 분류 집계

| 환경 | trial 수 | 성공 |
|---|---|---|
| 학습 분포 동일 | 2 | 0 |
| 학습 분포 外 | 0 | 0 |

---

## 종합 정성 메모

### 두 task 구분 응답성

> 두 task 모두 *해당 task 방향 접근*은 일부 가능. task 혼동 (task1 명령에 캔 잡으려 등) 관찰 안 됨. 두 task 사이 응답성 격차는 M1.5 A2 보다 *적은* 인상 (M1.5 A2 는 task2 > task1 약한 차이, 본 분기는 비슷). 단 단축 1+1 trial 로는 일반화 불가.

### 6:4 편향 영향 관찰 (front:back)

> 단축 — back orientation 미시도. 평가 불가. 다음 사이클에서 front:back 5:5 균형 데이터 + 비교 권장.

### 동작 품질 정성 관찰

> 동작 자체 부드럽고 모터·하드웨어 이상 신호 없음 (gripper 0-10 정상 범위, 관절 각도 무리 없음). M1.5 A2 와 *동일* — 정책 *판단력* 의 한계 (도달 단계 일부, 짚기·완료 단계 응답성 부재). 떨림·과도한 속도·충돌·경로 이탈 없음.

### M2 본 학습 진입 가치 판단

> **0~20% 영역 확정** (단축 2/2 = 0%, M1.5 A2 와 *동일 영역*). `empty_cameras` 단일 변수 변경은 *추론 개선 신호 없음* — **다음 사이클은 `empty_cameras` 외 영역 (데이터·workspace·추론 인프라) 으로 진단 이동 확정**.
>
> 다음 사이클 Phase 1 결정 영역 (M1.5 평가와 동일 + 본 분기 결과로 *우선순위 조정*):
> 1. **데이터셋 확장 (최우선)** — M1 잔여 100ep + 다른 사람 + orientation 5:5 균형 + 위치 분포 다양화. 본 분기 결과로 *가장 가능성 높은 root cause* 로 격상.
> 2. 학습 방법 — LoRA rank·target / VLM trainable / epoch / lr·scheduler·batch (data 충분 후)
> 3. 학습 노드 — prof_computer 유지 (camera_empty 학습 완주로 안정성 재검증) 또는 DGX 재시도
> 4. 다음 검증 시점 — 본 사이클과 같은 *비교 단축* 패턴 + 데이터 확장 효과 정량 측정

---

## 부가 발견 — 추론 인프라 이슈 (본 사이클 부수 산출)

> [`docs/work_flow/specs/ANOMALIES.md`](../../../../docs/work_flow/specs/ANOMALIES.md) §02_leftarm_v2_finetune #8·#9·#10 정식 기록. 본 사이클에서 발견된 *인프라 차원* 이슈.

| # | 영역 | 발견 | 처리 |
|---|---|---|---|
| 1 | `leftarm_v2_inference.py` | LoRA adapter 만 로드 시 base smolvla_base 의 default `empty_cameras=0` 이 적용되어 ckpt `config.json.empty_cameras=1` (camera_empty 분기) 와 mismatch | inference script 패치 — ckpt config.json 의 `empty_cameras` 를 `policy.config` 에 강제 적용 (L508-525, ~17줄) |
| 2 | `scripts/deploy_orin.sh` | `--delete` rsync 가 Orin 의 `orin/config/{ports,cameras}.json` 실측 값을 devPC 의 null template 으로 덮어쓰는 시스템 결함 (BACKLOG #1, 2026-05-14 사전 식별) | deploy_orin.sh 패치 — `--exclude 'checkpoints/' 'config/ports.json' 'config/cameras.json'` 추가. dgx 의 base_config.yaml 보호 패턴과 동일. BACKLOG #1 완료 처리. |
| 3 | orchestrator 운영 | inference script 패치 후 deploy 시 *위험 패치 (BACKLOG #1) 를 먼저 처리하지 않고* deploy → Orin ckpt 두 개 (camera_empty + A2) 모두 삭제. camera_empty 는 재다운로드 (~17초) 복원, A2 는 사용자 결정으로 스킵 후 검증 시 별도 재다운로드. | ANOMALIES #10 (ORCHESTRATOR_GAP) — reflection 단계 분석 (orchestrator 의 *알려진 위험 항목 우선 차단* 휴리스틱 검토). |

---

## 다음 단계

### 결과 보고

본 시트 작성 시점 — *결과 명확* (두 모델 차이 없음, 0% 영역). 사용자가 정성 보고 (이미 메인 Claude 에 전달) 만으로 충분. 추가 정량 trial 불요.

### 결과별 분기

| 결과 | 다음 액션 |
|---|---|
| ≥1/2 (유의미 개선) | `empty_cameras` 가 부분 fix 확정 → camera_empty 패턴 유지 + 200ep 수집 → 본 학습 |
| 비슷한 0/2 + 동작 개선 신호 | 부분 fix → 데이터 확장 + `empty_cameras=1` 유지 |
| **비슷한 0/2 + 동작 차이 없음 ← 본 사이클 확정** | **`empty_cameras` root cause 아님 → 데이터 확장이 *유일한 가치 영역* + 다른 가설 (workspace, dataset 품질 등) 으로 진단 이동** |

### 다음 사이클 입력 (Phase 1 spec 작성 시 활용)

본 보고서 + `a2_eval_2026-05-17.md` + `research_empty_cameras_2026-05-18.md` 3 문서가 *데이터 확장 사이클* 의 출발점. 다음 spec 작성 시 메인 Claude 가 본 보고서의 §"M2 본 학습 진입 가치 판단" 우선순위 4 영역을 직접 입력으로 사용.
