# Auto-Approved Actions Log — 05_interactive_cli

> 본 spec 사이클 자동화 진행 중 사용자가 임시 자동 승인 권한 부여한 작업의 추적 기록.
> 사용자 요청 (2026-05-01): "이번 작업에서 내가 allow 해야되는거 풀어줄테니까 너가 하고 기록만 따로 파일을 생성해서 기록해줘".
>
> 본 파일은 사후 검증·reflection 분석용. ANOMALIES.md 의 HOOK_BLOCK 형 신호와 짝.

## 정책

- 본 사이클 (05_interactive_cli) 진행 중에 한해, hook 또는 settings.json deny 외 사용자 prompt 가 필요한 작업을 메인 (orchestrator) 이 자율 진행
- Category A·D 절대 금지 영역은 본 정책과 무관 (계속 차단)
- 모든 자동 진행 항목은 본 파일에 시각·작업·이유 누적

## 형식

```
| # | 시각 | 작업 종류 | 도구 | 대상 | 이유 |
|---|------|-----------|------|------|------|
```

## 누적

| # | 시각 | 작업 종류 | 도구 | 대상 | 이유 |
|---|------|-----------|------|------|------|
| 1 | 2026-05-01 18:30 | 메타 — 본 파일 자체 생성 | Write | `docs/work_flow/context/auto_grants_05_interactive_cli.md` | 사용자 명시 요청 — 권한 승인 작업 추적용 별도 파일 신설 |
| 2 | 2026-05-01 18:30 | ANOMALIES.md 본 사이클 섹션 추가 | Edit | `docs/work_flow/specs/ANOMALIES.md` | 사용자 명시 요청 — "이번 작업의 reflection 에 너무 allow 를 많이 해야 되서 자동화가 잘 안된다" 기록 |
| 3 | 2026-05-02 12:30 | awaits_user-B ckpt 소스 조합 메인 자율 결정 | 사용자 답 (`권장사항대로`) 확장 적용 | O1 study 산출물 | 사용자 "권장사항대로" 답 — A·C 는 명시 권장 존재. B 의 ckpt 소스 조합 (HF Hub / 로컬 / 자동 탐색 / 기본값 4가지 중 어느 조합) 은 task-executor 명시 권장 없었음 → 메인이 합리적 default 결정: HF Hub repo_id + 로컬 ckpt 경로 + 기본값 `smolvla_base` 3개 조합 (자동 탐색은 구현 복잡 + 사용자 명시 합의 없어 제외). O2 task-executor 가 위 3개 조합으로 ckpt 선택 UI 구현. 사용자 사후 검증 시 변경 가능 |
| 4 | 2026-05-02 13:30 | Phase 3 D3 검증 사전 작업 — `~/.ssh/config` datacollector 항목 추가 | Edit | `~/.ssh/config` | datacollector 머신 실측값 (`smallgaint@172.16.133.102`, Ubuntu 22.04 LTS, MAC e4:70:b8:09:4c:ed) 기반 SSH alias 등록. orin·dgx 동일 패턴. 키 ed25519 공유 |
| 5 | 2026-05-02 13:30 | DataCollector ssh-copy-id 키 배포 + read-only 검증 | Bash (devPC + ssh datacollector) | datacollector 머신 | 사용자 `! ssh-copy-id datacollector` 1회 비밀번호 입력 → 키 인증 통과. 메인이 read-only 검증 자동 (디스크·메모리·CPU·GPU·USB·video·smolvla 디렉터리·.ssh·apt 패키지). 결과: GPU 없음(Intel HD 620), RAM 7G, 디스크 234G/149G 가용, /dev/video0·1 둘 다 노트북 내장, ~/smolvla 미존재, python3-venv·pip·dev·curl·ffmpeg·v4l-utils 미설치, dialout 그룹 미포함 |
| 6 | 2026-05-02 14:00 | docs/storage 정리 — 사용자 명시 요청 | Edit (4 파일) + Write (예정 2 파일) | `02_hardware.md` §1 + 새 §5 / `03_software.md` 새 §6 / `04_devnetwork.md` §1·§2·§3·§5·§6·§8·§9 / `scripts/dev-connect.sh` 1줄 / 신규 `07_datacollector_venv_setting.md` (task-executor) / 신규 `10_datacollector_structure.md` (task-executor) | 사용자 명시 요청 ("02·03·04 구조에 맞게 datacollector 정리 + venv_setting·structure 도 orin·dgx 동일 + dev-connect.sh 추가"). 02·03·04·dev-connect.sh 는 메인 직접. 15·16 신규는 05·06·07·08 패턴 미러로 task-executor 위임 |
| 7 | 2026-05-02 15:00 | docs/storage 재정렬 (의미적 그룹) — 사용자 명시 요청 | task-executor (mv 8건 + grep 일괄 갱신 + 09 분해 흡수 + 09 삭제) | `docs/storage/` 전 파일 + spec·BACKLOG·plan·log·todos·context/history 다수 | 사용자 명시 요청 ("숫자 다시 정렬 — storage 루트는 시간 순서가 아닌 종합본"). 노드별 그룹 모두 orin→dgx→datacollector 통일. 매핑: 15→07 / 07→08 / 08→09 / 16→10 / 10→11 / 11→12 / 12→15. 09 폐기 (모든 내용 02·03·04·07·10·11 에 분해 흡수). grep 검증 — 운영 문서 옛 패턴 0건 |
| 8 | 2026-05-02 15:30 | Category B 영역 — `scripts/deploy_datacollector.sh` + `datacollector/scripts/setup_env.sh` 정정 | 사용자 명시 동의 ("B good") | deploy_datacollector.sh: `DATACOLLECTOR_DEST` username 무관화 (`ssh ... 'echo $HOME'` 동적 결정) + 09 라인 제거 + 04_devnetwork.md 참조 변경. setup_env.sh: Python 3.12 가정 → Python 3.10 시스템 (07_datacollector_venv_setting 결정 정합) + python3.12-venv 의존 제거 (python3-venv·python3.10-venv 로 대체). 두 스크립트 `bash -n` 통과 + dry-run 통과 (`/home/smallgaint/smolvla` 자동 결정 확인) | 04 사이클 산출물 (deploy·setup_env) 의 username 하드코드 + python3.12 가정이 datacollector 실 환경 (smallgaint user, system Python 3.10) 와 불일치. 사용자 명시 동의 받아 정정. Coupled File Rules: pyproject.toml 미수정 → 02 diff 갱신 불필요 |
| 9 | 2026-05-02 15:30 | DataCollector 첫 deploy 실행 | Bash (devPC `bash scripts/deploy_datacollector.sh`) | datacollector 머신 `/home/smallgaint/smolvla/{datacollector,docs/reference/lerobot}` | 5.4MB 압축 전송, 11.9MB total. datacollector/{interactive_cli·scripts·config·tests·README·pyproject.toml} + docs/reference/lerobot/ 모두 동기화 성공. SSH alias·DEST 자동 결정·sudo 디렉터리 사전 생성 정상 |
| 10 | 2026-05-02 15:50 | Category B 영역 — `datacollector/pyproject.toml` requires-python 완화 | 사용자 명시 동의 ("B good" 모드 연장) | `datacollector/pyproject.toml:9` `>=3.12` → `>=3.10` | setup_env.sh 실 실행 시 `ERROR: Package 'lerobot' requires a different Python: 3.10.12 not in '>=3.12'` 발생 — 04 D1 가정 (09 §2-1 Python 3.12) 가 코드까지 박힌 결과. 새 07_datacollector_venv_setting.md 결정 (Python 3.10 시스템) 와 정합. orin/pyproject.toml `>=3.10` 일관성 확보. upstream lerobot `>=3.12` 는 wrapper 패키지 (`name = "lerobot"`) 로 우회됨 — datacollector/lerobot symlink 가 code 만 제공, requires-python 체크는 datacollector/pyproject.toml 만 |
| 11 | 2026-05-02 15:55 | 재 deploy (pyproject.toml 갱신만 sync) | Bash (devPC `bash scripts/deploy_datacollector.sh`) | datacollector 머신 | rsync incremental — 변경된 pyproject.toml 만 빠르게 sync |
| 12 | 2026-05-02 16:30 | DataCollector setup_env.sh 실행 + venv 셋업 완료 | 사용자 직접 실행 (sudo apt + ~700MB torch 다운로드) | datacollector `~/smolvla/datacollector/.hylion_collector` | torch 2.11.0+cu130 + torchvision 0.26.0+cu130 + lerobot 0.5.2 + datasets 4.8.5 + scservo-sdk + 9 entrypoint 모두 OK. CUDA 13 wheel 받혔지만 GPU 없어 cuda_avail=False (CPU-only 동작). nvidia-* dep 2.7GB dead weight (BACKLOG #10 다음 사이클 정리) |
| 13 | 2026-05-02 17:00 | USB 디바이스 진단 + USB 2.0 hub 대역폭 한계 발견 | Bash (ssh datacollector lsusb·v4l2-ctl·ffmpeg 진단) | (read-only) | 사용자 USB hub 가 USB 3.0 이지만 카메라·SO-ARM 자체가 USB 2.0 → Bus 01 (480Mbps) 단일 풀 공유 → lerobot-find-cameras 동시 capture 시 video4 read_failed. 해결: lerobot OpenCVCameraConfig.fourcc=MJPG 강제 (압축 ~1/10 → 대역폭 여유) |
| 14 | 2026-05-02 17:15 | record.py + env_check.py 확장 — 사용자 요청 + 진단 대응 | Edit (메인 자율) + 재 deploy | `record.py` cameras_str 에 `fourcc: MJPG` 추가 / `env_check.py` 5단계 → 7단계 (§6 모터 ID 등록 ping + §7 calibration JSON 파일 존재) | 사용자 명시 요청 ("모터 ID·calibration 도 env_check 에 포함"). MJPG 는 USB 2.0 hub 단일 사용 시 카메라 2대 동시 capture 보장. §6 는 scservo_sdk PortHandler·PacketHandler 로 1~6 ping. §7 는 `~/.cache/huggingface/lerobot/calibration/{robots,teleoperators}/{type}/{id}.json` 파일 존재 확인 (lerobot/robots/robot.py:50, teleoperators/teleoperator.py:50 직접 인용) |
| 15 | 2026-05-02 17:30 | env_check `_check_cameras()` 외부 카메라 우선 + range 확장 | Edit (메인 자율) | range(4) → range(10) + 외부 카메라 (idx≥2) 우선 매핑 | 기존 range(4) 가 video4 (YJX-C5) 못 찾음 + video0·1 (내장) 가 wrist 로 잘못 매핑됨. 외부 카메라 우선 로직으로 wrist_left=2, overview=4 자동 매핑 (datacollector 실측 정합) |
| 16 | 2026-05-02 17:30 | env_check 7단계 동작 확인 (사용자 ssh 호출) | Bash (ssh datacollector ... flow2_env_check) | (read-only) | PASS 5건 (venv·USB·카메라·data_dir·모터 ID 1~6) + FAIL 2건 (lerobot import PEP 695 SyntaxError + calibration 미수행). 모터 ID 등록은 사용자 출하 또는 04 D2 시점에 이미 완료됨 (사용자 추가 작업 불필요). |
| 17 | 2026-05-02 17:45 | Category B 영역 — pyproject.toml + setup_env.sh **재정정** (옵션 A — Python 3.12) | 사용자 명시 동의 ("A로 가자") | `requires-python` `>=3.10` → `>=3.12` 복구 / setup_env.sh Python 3.12 우선 + python3.12-venv 의존성 복구 + python3.10/python3 fallback 제거 (deadsnakes PPA 사전 설치 명확 가이드 추가) | 항목 8·10·11 의 옵션 B (`>=3.10` 우회) 가 잘못된 판단으로 입증됨 — lerobot upstream 5+ 파일 (utils/io_utils.py:93, datasets/streaming_dataset.py:58, processor/pipeline.py:255, motors/motors_bus.py:51,52) 가 PEP 695 generic syntax 사용 → Python 3.12+ 강제. 04 D1 의 "Python 3.12 권장" 가정이 사실 정답. CONSTRAINT 재정렬: 본 사이클의 reflection 분석 핵심 학습 신호. |

(사이클 진행에 따라 누적)
