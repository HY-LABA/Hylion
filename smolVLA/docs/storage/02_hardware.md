# smolVLA 하드웨어 현황 (현재 보유/실측)

> 작성일: 2026-04-21  
> 목적: 실제 보유 장비와 실측 하드웨어 값을 기록

## 1) 컴퓨팅 장치

- 개발 PC: Ubuntu 환경 사용 중
- 엣지 장치: `Jetson Orin Nano Super Developer Kit`
- 학습/파인튜닝 서버: `NVIDIA DGX Spark`

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

## 5) SO-ARM 핵심 부품 (BOM 기준) — **Arm Kit Pro**

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

## 6) 카메라 (SO-ARM용)

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

## 7) 로봇 구성 수량

- Follower arm: 1대
- Leader arm: 1대
- Camera: 2대
