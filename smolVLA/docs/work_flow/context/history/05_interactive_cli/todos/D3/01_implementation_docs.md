# D3 — Implementation (docs)

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

DataCollector 노드 문서 정리 — `07_datacollector_venv_setting.md` + `10_datacollector_structure.md` 신규 작성. 02·03·04 (orin/dgx) 구조와 동일 패턴 미러.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/07_datacollector_venv_setting.md` | A (신규) | DataCollector venv 세팅 — 05·06 패턴 미러, CPU-only torch 선택 근거, 미셋업 TODO 마킹 |
| `docs/storage/10_datacollector_structure.md` | A (신규) | datacollector/ 구조 + 컴포넌트 책임 + 마이그레이션 계획 — 07·08 패턴 미러 |
| `docs/storage/09_datacollector_setup.md` | M (최소 수정) | 헤더에 15·16 참조 안내 한 줄 추가 (본문 변경 없음) |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미수정 — 해당 없음 (docs/storage/ 신규 파일)
- CLAUDE.md Hard Constraints Category B: `pyproject.toml`·`setup_env.sh`·`deploy_*.sh` 미수정 — 해당 없음
- CLAUDE.md 옛 룰: `docs/storage/` 하위 bash 명령 예시 추가 자제 — 준수 (setup_env.sh 절차 인용에 한정)
- Coupled File Rule: orin/lerobot/ 미수정 — 해당 없음
- 레퍼런스 활용: 05·06·07·08·09 직접 Read 후 구조·절 번호·표 형식 미러

## 05·06 패턴 미러 결과 (15 에 적용)

| 05·06 절 | 15 에서 처리 | 변형 내용 |
|---|---|---|
| §1 개요 (venv 이름·위치·Python·역할) | §1 개요 | `.hylion_collector`, `~/smolvla/datacollector/`, Python 3.10 시스템. Orin JP 6.0 wheel / DGX 3.12 와의 차이 명시 |
| §2 venv 환경 구성 (선택 근거·extras·패키지 표) | §2 venv 환경 구성 | extras: record+hardware+feetech (smolvla·training 제외). orin subset 위치 명시. 실측 패키지 표 = TODO |
| §3 PyTorch 설치 방식 (선택 근거·설치 순서) | §3 PyTorch 설치 방식 | CPU-only wheel 선택 근거 (GPU 없음). 노드별 3-way 비교 표 추가. LD_LIBRARY_PATH 패치 불필요 명시 |
| §4 setup_env.sh 구성 세팅 | §4 setup_env.sh 구성 세팅 | §0~§5 섹션 구조 유지. Orin 대비 차이 열 추가. 환경변수: HF_HOME 만 (GPU 없으므로 CUDA 관련 없음) |
| §5 잔여 리스크 | §5 잔여 리스크 / 후속 검증 | 미셋업 항목 표 + Python 버전 불일치 주의 + lerobot/ 옵션 B 미진행 + DHCP·HF Hub 리스크 |
| §6~§8 검증 결과 (DGX) | 해당 없음 | 미셋업 상태이므로 검증 결과 섹션 미작성 |
| 변경 이력 | §6 변경 이력 | 초안 작성 이력 1건 |

## 07·08 패턴 미러 결과 (16 에 적용)

| 07·08 절 | 16 에서 처리 | 변형 내용 |
|---|---|---|
| §0 본 문서의 위치 | §0 본 문서의 위치 | DataCollector 단일 책임 명시. 옵션 B 미진행 상태 명시 |
| §1 디렉터리 트리 (현재 vs 새 구조) | §1 디렉터리 트리 (현재) | 현재 (2026-05-02 실측) + 목표 구조 두 가지. interactive_cli/ 05 산출물 포함 |
| §2 핵심 컴포넌트 책임 표 | §2 핵심 컴포넌트 책임 표 | 완료·미진행·도입 시점 열 추가. lerobot/ 미존재 상태 명시 |
| §3 마일스톤별 책임 매트릭스 | §3 마일스톤별 책임 매트릭스 | 04~08 마일스톤 5열. interactive_cli/ 를 05 열에 반영 |
| §4 외부 의존성 | §4 외부 의존성 | devPC sync hub + HF Hub + DataCollector↔DGX 전송 + 시스템 의존성 (실측 기반) |
| §5 마이그레이션 계획 | §5 마이그레이션 계획 | 완료·미진행 두 분류. lerobot/ 옵션 B 계획 상세 (향후 todo 명시) |
| §6 후속 TODO 트리거 | §6 후속 TODO 트리거 | G3·lerobot 옵션 B·06 마일스톤 등 |
| 변경 이력 | 변경 이력 | 초안 작성 이력 1건 |

## "셋업 후 채울 항목" 표 (15 의 미실측 항목)

| 항목 | 현재 | 갱신 조건 |
|---|---|---|
| torch 실제 버전 | 미셋업 | `pip show torch` |
| torchvision 버전 | 미셋업 | `pip show torchvision` |
| datasets 버전 | 미셋업 | `pip show datasets` |
| feetech-servo-sdk 버전 | 미셋업 | `pip show feetech-servo-sdk` |
| 전체 설치 목록 | 미셋업 | `pip freeze` |
| 셋업 소요 시간 | 미셋업 | `time bash setup_env.sh` |
| 디스크 사용량 (.hylion_collector/) | 미셋업 | `du -sh .hylion_collector/` |
| CPU thread 수 | 미실측 | `torch.get_num_threads()` |
| Python 실제 버전 | 3.10.12 (실측 2026-05-02) | 셋업 후 재확인 |

## 잔여 리스크

1. **datacollector/lerobot/ 옵션 B 미진행**: 04·05 사이클 모두 스코프 외. `setup_env.sh` 의 upstream symlink 로 임시 처리. 향후 별도 todo 에서 curated subset 구성 + `05_datacollector_lerobot_diff.md` 신규 작성 필요.

2. **Python 버전 불일치 (pyproject.toml vs 실측)**: `datacollector/pyproject.toml` 의 `requires-python = ">=3.12"` 와 실측 시스템 Python 3.10.12 가 불일치. 실물 셋업 시 옵션 A (deadsnakes PPA Python 3.12 추가) 또는 옵션 B (pyproject.toml `>=3.10` 으로 조정) 중 선택 필요.

3. **미설치 시스템 패키지**: `python3-venv`, `python3-pip`, `ffmpeg`, `v4l-utils` 등. setup_env.sh 실행 전 사전 설치 필요.

4. **dialout 그룹 미포함**: SO-ARM USB 직렬 포트 접근에 필요. 셋업 전 추가 필요.

5. **09_datacollector_setup.md 와의 중복**: 09 는 04 사이클 설계 결정 원본으로 보존. 15·16 의 신규 정보는 09 와 일부 중복되나 의도적. 09 본문에 15·16 참조 안내 1줄 추가 완료.

## code-tester 입장에서 검증 권장 사항

- 마크다운 문법: 15·16 의 헤딩 레벨·표 정렬·코드 블록 종료 확인
- 절 번호 일관성: 15 가 05·06 의 `## 1) 개요`, `## 2) venv`, `## 3) PyTorch`, `## 4) setup_env`, `## 5) 리스크` 와 일관하는지
- 16 이 07·08 의 `## 0)`, `## 1)`, `## 2)`, `## 3)`, `## 4)`, `## 5)` 와 일관하는지
- 추측 작성 미포함 여부: 실측값 없는 항목은 모두 "TODO: 셋업 후 기재" 또는 "(TODO: 셋업 진행 후 갱신)" 명시됐는지
- 노드별 차이점 명확성: Orin (aarch64+JetPack/CUDA) / DGX (aarch64+CUDA13) / DataCollector (x86_64+CPU only) 가 15 §3 표에서 명시됐는지
- 09 변경 최소화: 헤더 참조 안내 1줄만 추가됐는지 (본문 변경 없음)
