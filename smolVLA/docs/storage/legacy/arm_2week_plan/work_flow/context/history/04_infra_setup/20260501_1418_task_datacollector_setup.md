# 20260501_1418 — TODO-D1 DataCollector 노드 정체 + 디렉터리 신규

> 작성: 2026-05-01 14:18 | task-executor | cycle: 1
> 담당 TODO: D1 (study)

## 이벤트 요약

DataCollector 노드 설계 결정 문서 (`docs/storage/09_datacollector_setup.md`) 작성.
사용자 awaits_user 4건 답변 (별도 PC 신규 구매 / Ubuntu 22.04 LTS / datacollector/ / pyproject 신규 작성 / HF Hub+rsync 둘 다) 을 반영.

## 사전 점검

| 확인 항목 | 결과 |
|---|---|
| lerobot upstream pyproject [project.optional-dependencies] | extras 키 확인: dataset / training / hardware / core_scripts / feetech / smolvla / intelrealsense 등 |
| orin/pyproject.toml extras 분석 | smolvla + hardware + feetech (학습 의존성 제외됨) |
| 04_devnetwork.md SSH 패턴 | Host alias / HostName / User / Port / IdentityFile / ServerAliveInterval 패턴 추출 |
| 05_orin_venv_setting.md venv 패턴 | .hylion_arm / Python 3.10 / setup_env.sh 패턴 추출 |
| 08_orin_structure.md 대칭 패턴 | §0 변경이력 + §1~§5 + §6 향후 + §7 변경이력 표 구성 확인 |
| 09_dgx_structure.md 대칭 패턴 | 동일 절 구성 확인 |

## 주요 결정

- DataCollector 노드: 별도 PC 신규 구매 / Ubuntu 22.04 LTS / x86_64
- 디렉터리: `smolVLA/datacollector/` (orin·dgx 형제 패턴)
- venv 이름: `.hylion_collector` (orin=.hylion_arm, dgx=.arm_finetune 패턴 미러)
- pyproject extras: record + hardware + feetech (smolvla·training 제외)
- lerobot entrypoint: record / replay / teleoperate / calibrate / setup-motors / find-cameras / find-port / find-joint-limits / info (eval·train 제외)
- 데이터 전송: HF Hub + rsync 둘 다 지원 (TODO-T1 입력)

## 산출물

- `docs/storage/09_datacollector_setup.md` 신규 작성

## BACKLOG 자연 해소

- BACKLOG 04 #2 (.archive 컨벤션) — run_teleoperate.sh 최종 이동 시점 명시 (TODO-D2)
- BACKLOG 02 #1 (DHCP 예약) — DataCollector 동일 카테고리 §4 명시 (사용자 책임)
