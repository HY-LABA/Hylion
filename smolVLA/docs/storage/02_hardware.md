# smolVLA 하드웨어 현황 (현재 보유/실측)

> 작성일: 2026-04-21  
> 목적: 실제 보유 장비와 실측 하드웨어 값을 기록

## 1) 컴퓨팅 장치

- 개발 PC: Ubuntu 환경 사용 중
- 엣지 장치: `Jetson Orin Nano Super Developer Kit`
- 학습/파인튜닝 서버: `NVIDIA DGX Spark`
- 데이터 수집 PC (DataCollector): x86_64 노트북 (Intel Core i3-7100U, GPU 없음 — Intel HD 620 only)

## 2) devPC 사양 확인 방법 및 실측

### 실측 결과 (2026-04-21)

- 호스트명: `babogaeguri-950QED`
- OS: `Ubuntu 22.04.5 LTS`
- 커널: `6.8.0-106-generic`
- CPU: `12th Gen Intel(R) Core(TM) i7-1260P`
  - 논리 코어: `16`
  - 소켓당 코어: `12`
- 메모리: 총 `15Gi` (가용 약 `8.1Gi`, 점검 시점)
- GPU:
  - `nvidia-smi not found` (NVIDIA 드라이버/CLI 미탐지 상태)
- 저장장치:
  - 내장 NVMe: `SAMSUNG MZVL2512HCJQ-00B` `476.9G`
  - Linux 루트(`/`): `nvme0n1p5` (`ext4`, `200G`)
  - EFI: `nvme0n1p1` (`vfat`, `200M`)
  - 추가 USB mass storage 디바이스(`sda`, `sdb`)가 보이지만 크기 `0B`로 인식됨

## 3) Orin 저장장치 실측

- 스냅샷 파일:
  - `smolVLA/docs/storage/devices_snapshot/orin_env_snapshot_2026-04-21_1316.txt`
  - `smolVLA/docs/storage/devices_snapshot/orin_storage_snapshot_2026-04-21_1323.txt`
- 확인된 디스크:
  - `nvme0n1` `SAMSUNG MZVL2256HCHQ-00B` (256GB급)
  - 루트(`/`) 마운트: `nvme0n1p1` (`ext4`)
  - EFI 마운트: `nvme0n1p10` (`vfat`)
- 메모:
  - 외장 SSD 별도 장치는 스냅샷 시점에서 식별되지 않음 (`/dev/sdX` 또는 추가 `nvmeXnY` 미검출)

## 4) DGX Spark 실측

> 스냅샷: `smolVLA/docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt`

| 항목 | 실측값 | 비고 |
|---|---|---|
| 호스트명 | `spark-8434` | |
| OS | `Ubuntu 24.04.4 LTS` | |
| 커널 | `6.17.0-1014-nvidia` | |
| CPU | `aarch64` 20코어 | NUMA 1노드, Max 3900 / 2808 MHz (클러스터별) |
| 메모리 | 공식 `128 GB LPDDR5x`, Linux 실측 `121Gi` | UMA/coherent unified system memory. 스냅샷 시점 `MemAvailable` 약 90Gi, swap `0B` |
| GPU 모델 | `NVIDIA GB10` | Grace Blackwell |
| GPU 메모리 | 전용 VRAM 없음 | CPU/GPU가 동일 LPDDR5x 메모리 풀 공유. `nvidia-smi` VRAM 총량은 `[N/A]`/`Not Supported`가 정상 |
| GPU 드라이버 | `580.142` | CUDA 13.0 지원 |
| 저장장치 | NVMe `3.7T` | 루트(`/`) 사용 228G / 가용 3.3T, 외장 SSD 미마운트 |

---

## 5) DataCollector 실측 (2026-05-02)

| 항목 | 실측값 | 비고 |
|---|---|---|
| 호스트명 | `smallgaint` | |
| 사용자명 | `smallgaint` | |
| OS | `Ubuntu 22.04 LTS` | x86_64 |
| 커널 | `6.8.0-106-generic` (HWE) | unattended-upgrade 5월 02 적용 |
| CPU | `Intel(R) Core(TM) i3-7100U @ 2.40GHz` | 4 코어 (2 phys × 2 thread), Max 2400 MHz |
| 메모리 | 총 `7Gi` (가용 약 `6Gi`) | swap `1Gi` |
| GPU | `Intel HD Graphics 620` (내장) | NVIDIA 없음 — PyTorch CPU wheel only |
| 저장장치 | NVMe `/dev/nvme0n1p2` `234G` | 사용 73G / 가용 149G (33% used) |
| WiFi MAC | `e4:70:b8:09:4c:ed` (`wlp1s0`) | DHCP (172.16.133.x 학교 대역) |
| 내장 카메라 | `/dev/video0`·`/dev/video1` 720p HD (Namuga, Silicon Motion ID `2232:1083`) | UVC, 외부 USB 웹캠은 별도 연결 필요 |
| 추가 USB 장치 | `Samsung Fingerprint (04e8:7301)`, `Intel Bluetooth (8087:0a2b)` | 본 프로젝트 무관 |
| Python | `3.10.12` (시스템) | venv 별도 (`.hylion_collector`) |

DataCollector 의 핵심 책임: SO-ARM teleoperation 기반 데이터 수집 (`lerobot-record`) + HF Hub push 또는 DGX 로 rsync 전송. GPU 없어도 무관 (추론·학습 X). 외부 USB 카메라 1~2대 (top·wrist 시점) 연결이 데이터 수집 사전 조건.

### 5-1) USB 토폴로지·대역폭 학습 (2026-05-02 실측)

**관찰**: SO-ARM 2대 + 외부 USB 카메라 2대 (총 4 디바이스) 를 **단일 USB hub** 통해 노트북 USB 3.0 포트에 연결. `lsusb -t` 결과:

```
Bus 02 (USB 3.0, 5000M)  ← 사용자 USB 3.0 hub 의 USB 3.0 path (Realtek RTS5411 hub)
  └─ hub (5000M) → hub (5000M)  ← 비어있음 (USB 3.0 디바이스 없음)

Bus 01 (USB 2.0, 480M)   ← USB 2.0 path — 모든 디바이스 종속
  └─ Realtek RTS5411 hub (480M)
        ├─ video2·3 (YJXU502S 5M USB CAM, 480M, vendor 0edc:2050)
        ├─ video4·5 (GYY YJX-C5, 480M, vendor 0bda:0565)
        ├─ ttyACM0 / ttyACM1 (QinHeng 1a86:55d3 USB Single Serial, 12M each — SO-ARM)
        └─ ...
```

**핵심 포인트**: USB 3.0 hub 가 USB 2.0 디바이스 (UVC 카메라·CDC ACM serial 등) 를 받으면 **자동으로 USB 2.0 path (Bus 01) 로 enum**. 즉 USB 3.0 hub + USB 3.0 케이블 + USB 3.0 노트북 포트 충족해도 **카메라·SO-ARM 자체가 USB 2.0 only 디바이스라서 480 Mbps 대역폭 한계 강제**.

### 5-2) USB 2.0 대역폭 경합 → MJPG fourcc 강제 패턴

**문제 — `lerobot-find-cameras opencv` 동시 capture 시 read_failed**:

| Format | 카메라당 대역폭 | 2대 동시 |
|---|---|---|
| YUYV 640×480@30fps (lerobot OpenCV default) | ~147 Mbps | ~294 Mbps + SO-ARM 2대 = USB 2.0 한계 근접 → read_failed |
| **MJPG 640×480@30fps** | **~10~15 Mbps** | **~30 Mbps + SO-ARM = 여유 충분** |

**해결 — `OpenCVCameraConfig.fourcc=MJPG` 강제** (`docs/reference/lerobot/src/lerobot/cameras/opencv/configuration_opencv.py:65`):

```python
# datacollector/interactive_cli/flows/record.py
cameras_str = (
    f"{{wrist_left: {{type: opencv, index_or_path: {idx}, "
    f" width: 640, height: 480, fps: 30, fourcc: MJPG}}, "
    f" overview: {{...}}}}"
)
```

→ MJPG 가 lerobot-record 의 `--robot.cameras` draccus 인자에 명시되어 카메라 2대 동시 capture 가능. **orin·datacollector 모두 동일 패턴 적용 권장** — 외부 USB 카메라 다중 사용 시 default fourcc 로 채택.

### 5-3) `env_check` 7단계 통합 패턴 (2026-05-02 — 사용자 요청 §6·§7 추가)

`datacollector/interactive_cli/flows/env_check.py` 의 `flow2_env_check()` 가 7단계로 통합 — 04 G3 (DataCollector check_hardware 이식) + G4 (실측 검증) 자연 흡수:

| 단계 | 검증 항목 | 패턴 |
|---|---|---|
| 1 | venv 활성화 (`.hylion_collector`) | 04 G1 step_venv 미러 |
| 2 | USB 시리얼 포트 (`/dev/ttyACM0·1`) | 04 G1 step_soarm_port 미러 |
| 3 | 카메라 인덱스 (외부 우선 — `idx≥2`, range 0~9) | 신규 — datacollector 노트북 내장 카메라 회피 |
| 4 | lerobot import (`lerobot.datasets.lerobot_dataset.LeRobotDataset`) | 04 G1 step_cameras 의 ImportError 패턴 미러 |
| 5 | 데이터 저장 경로 (`~/smolvla/datacollector/data/`) | 신규 — DataCollector 책임 |
| **6** | **SO-ARM 모터 ID 1~6 등록** (scservo_sdk PortHandler·PacketHandler ping) | **사용자 요청 추가** — `lerobot-setup-motors` 완료 확인 |
| **7** | **Calibration JSON 파일 존재** (follower + leader) | **사용자 요청 추가** — `~/.cache/huggingface/lerobot/calibration/{robots,teleoperators}/{type}/{id}.json` 검사 (`lerobot/robots/robot.py:50`, `teleoperators/teleoperator.py:50` 인용) |

**적용 가능 영역**: orin·dgx 의 env_check 도 같은 7단계 패턴 미러 가능 — 노드별 책임 맞춤 (orin = 추론용 ckpt 존재 검사, dgx = 학습용 데이터셋 cache 검사 등). 차기 사이클 reflection 후보.

## 6) SO-ARM 핵심 부품 (BOM 기준) — **Arm Kit Pro**

- 키트 등급: **Arm Kit Pro** (팔로워 12V 구성)
- 모터 계열: `Feetech STS3215`

| 구성 | 상세 모델 | 수량 |
|---|---|---|
| SO-101 follower (팔 1개) | `STS3215 12V, 1/345 gear (C018 또는 C047)` | x6 |
| SO-101 leader (팔 1개) | `STS3215 7.4V, 1/191 (C044)` | x2 |
| SO-101 leader (팔 1개) | `STS3215 7.4V, 1/345 (C001)` | x1 |
| SO-101 leader (팔 1개) | `STS3215 7.4V, 1/147 (C046)` | x3 |

> 팔로워 F1–F6은 Arm Kit Pro 기준 12V 모터(C018 또는 C047) 중 택일. 리더 L1–L6은 7.4V 모터 혼합 구성(C044 x2 / C001 x1 / C046 x3).

leader + follower(현재 보유 1쌍) 합계:
- `C018 또는 C047 x6` (follower, 12V)
- `C001 x1`, `C044 x2`, `C046 x3` (leader, 7.4V)

- 전원 공급:
  - **Follower arm**: **DC 12V** (Arm Kit Pro)
  - **Leader arm**: **DC 5V**
  - 커넥터: `5.5mm × 2.1mm DC 잭`

- 모터 드라이버(컨트롤 보드):
  - `Serial Bus Servo Driver Board, for ST/SC Series Serial Bus Servos`
  - 유통명 예시: `Waveshare Bus Servo Adapter (A)`
  - BOM 링크 ASIN 예시: `B0CTMM4LWK`
  - 수량 기준: 팔 1개당 보드 1개

- 보드-PC 연결 USB 케이블:
  - USB-A to USB-C 케이블
  - 상품 예시: `etguuds USB A to USB C Cable 6.6ft, 2-Pack, 3A`
  - ASIN 예시: `B0B8NWLLW2`

## 7) 카메라 (SO-ARM용)

- 모델: `OV5648 USB Camera Module`
- 수량: 2대 (SO-ARM 관측용)
- 구매 사양: 68° 버전 (제품 라인업: 68° / 120° 두 종 존재)

| 항목 | 값 |
|---|---|
| 센서 | OV5648 |
| 렌즈 크기 | 1/4 inch |
| 픽셀 크기 | 1.4μm × 1.4μm |
| 최대 유효 화소 | 2592(H) × 1944(V) = 5MP |
| 출력 포맷 | MJPEG / YUV2 (YUYV) |
| 지원 해상도·프레임 | 30fps UXGA, 15fps UXGAYUV |
| S/N 비 | 38dB |
| 다이내믹 레인지 | 68dB @ 8x gain |
| 감도 | 600mV/Lux-sec |
| 최저 조도 | 0.1lux |
| 셔터 | Electronic Rolling Shutter |
| 인터페이스 | USB 2.0 High Speed |
| USB 프로토콜 | USB 2.0 HS/FS |
| 드라이버리스 | USB Video Class (UVC) |
| OTG | USB 2.0 OTG |
| 화각 | 72° (스펙 시트 기준) / 제품 표기 68° — 실물 확인 필요 |
| 포커스 | Fixed Focus (스펙 시트 기준, 제품명 "Auto Focus"와 불일치 — 실물 확인 필요) |
| 부가 기능 | Flash Light, Microphone 내장 |
| 전원 | USB BUS POWER 5P 1.0mm Socket, DC 5V, 140mA |
| 동작 온도 | -20 ~ 70°C |
| 보관 온도 | 0 ~ 50°C |
| 호환 OS | Windows XP/Vista/7/8.1/10, Linux with UVC (≥2.6.26), Android 4.0+ with UVC |

## 8) 로봇 구성 수량

- Follower arm: 1대
- Leader arm: 1대
- Camera: 2대
