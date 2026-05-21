# NUC 하드웨어 / 소프트웨어 사양서

> Hylion 휴머노이드 로봇 저수준(low-level) 제어용 온보드 컴퓨터(NUC) 사양 정리
> 작성일: 2026-05-20 · 호스트명: `laba-desktop`

---

## 0. 한눈에 보기

| 항목 | 내용 |
|------|------|
| 제품 형태 | 미니 PC (Intel N95 기반, 데스크톱 섀시) |
| 정확한 제품명 | **확인 불가** — 제조사가 DMI/펌웨어 필드를 채우지 않음 (아래 1번 참조) |
| OS | Ubuntu 22.04.5 LTS (Jammy Jellyfish), 64-bit |
| 커널 | Linux 6.18.19-rt-x64v3-xanmod1 (**실시간 PREEMPT_RT / XanMod**) |
| CPU | Intel N95 (Alder Lake-N), 4코어 4스레드, 최대 3.4 GHz |
| GPU | Intel UHD Graphics (내장, Alder Lake-N) — 별도 외장 GPU 없음 |
| RAM | 16 GB (시스템 인식 15 GiB), 단일 모듈 + 2 GB 스왑 |
| 저장장치 | NVMe SSD 256 GB (M.2) |
| 네트워크 | 기가비트 유선 LAN (Realtek) + Tailscale VPN, 무선랜 없음 |
| 미들웨어 | ROS 2 Humble |

---

## 1. 제품 식별 정보 (중요)

이 기기는 **제조사(OEM)가 SMBIOS/DMI 정보를 입력하지 않은 화이트박스 미니 PC**입니다.
따라서 시스템 펌웨어에서 읽어낼 수 있는 "정확한 제품명"이 존재하지 않습니다.

```
시스템 제조사   : To be filled by O.E.M
제품명          : To be filled by O.E.M
제품 버전       : To be filled by O.E.M
메인보드 제조사 : To be filled by O.E.M
메인보드 모델   : To be filled by O.E.M
제품 SKU        : To be filled by O.E.M
섀시 제조사     : To be filled by O.E.M
```

확인 가능한 펌웨어 정보는 다음과 같습니다:

| 항목 | 값 |
|------|-----|
| BIOS 제조사 | American Megatrends International, LLC. (AMI) |
| BIOS 버전 | `IAN15001` |
| BIOS 날짜 | 2025-02-28 |
| 섀시 타입 | 3 (Desktop) |

> **참고:** Intel N95 + AMI BIOS `IAN15001` 조합은 시중에 여러 브랜드(무명/OEM 리브랜드)로 동일하게 유통되는 "N95 미니 PC" 계열입니다. 정확한 모델명·시리얼은 **기기 하단의 제품 라벨/스티커**나 구매 영수증으로 확인해야 합니다. (시스템 소프트웨어로는 식별 불가)

---

## 2. CPU

| 항목 | 값 |
|------|-----|
| 모델명 | Intel(R) N95 (Alder Lake-N, 12세대 계열) |
| 아키텍처 | x86_64 |
| 코어 / 스레드 | 4코어 / 4스레드 (코어당 1스레드, HT 없음) |
| 기본~최대 클럭 | 800 MHz ~ 3400 MHz |
| CPU 패밀리 / 모델 / 스테핑 | 6 / 190 / 0 |
| L1 캐시 | 128 KiB (d) + 256 KiB (i) |
| L2 캐시 | 2 MiB |
| L3 캐시 | 6 MiB |
| 가상화 | VT-x 지원 |
| 주요 명령어셋 | SSE4.2, AVX, AVX2, AVX-VNNI, FMA, AES-NI, SHA-NI, BMI1/2 |

> N95는 전부 효율(E)코어로 구성된 저전력 SoC입니다. 별도 P코어가 없어 단일 스레드 부하·실시간 제어 루프 설계 시 코어 4개 한도를 고려해야 합니다.

---

## 3. GPU / 그래픽

| 항목 | 값 |
|------|-----|
| GPU | Intel UHD Graphics (내장, Alder Lake-N) |
| PCI ID | `8086:46D2` (PCI 주소 `00:02.0`) |
| 커널 드라이버 | `i915` (모듈: i915, xe) |
| 외장 GPU | **없음** |
| NVIDIA / CUDA | **없음** (`nvidia-smi` 미설치, CUDA 미지원) |
| 디스플레이 출력 | DisplayPort ×1, HDMI ×2 |

> 외장 GPU·CUDA가 없으므로 머신러닝 추론은 **CPU 전용**입니다. 정책(policy) 추론은 ONNX Runtime / PyTorch CPU 빌드로 수행됩니다 (6번 참조).

---

## 4. 메모리 (RAM)

| 항목 | 값 |
|------|-----|
| 총 용량 | 16 GB (OS 인식 15 GiB) |
| 모듈 구성 | 단일 모듈 (lshw 기준 1개) |
| 메모리 타입 | 미확인 — 정확한 타입(DDR4/DDR5/LPDDR5)·속도는 `sudo dmidecode -t memory`로 확인 필요 |
| 스왑 | 2 GB (`/swapfile`, 파일 기반) |
| 현재 사용량(조회 시점) | 사용 4.7 GiB / 가용 9.8 GiB |

> Intel N95 플랫폼은 보통 단일 채널 메모리입니다. 정확한 타입·클럭은 root 권한이 필요해 이번 조사에서는 읽지 못했습니다.

---

## 5. 저장장치 / 네트워크 / 주변장치

### 5.1 저장장치
| 장치 | 내용 |
|------|------|
| `nvme0n1` | M.2 NVMe SSD, 256 GB (238.5 GiB) |
| `nvme0n1p1` | EFI 시스템 파티션, 512 MB → `/boot/efi` |
| `nvme0n1p2` | 루트 파티션, 238 GiB → `/` |
| 루트 사용량 | 234 GB 중 29 GB 사용 / 193 GB 여유 (13%) |

### 5.2 네트워크
| 항목 | 값 |
|------|-----|
| 유선 LAN | Realtek RTL8111/8168/8411 PCIe 기가비트 이더넷 (rev 15) |
| 인터페이스 | `enp1s0` — IP `192.168.0.8/24` |
| VPN | Tailscale (`tailscale0`) — IP `100.72.117.116` |
| 무선랜(Wi-Fi) | **감지되지 않음** |

### 5.3 USB / 주변장치
- USB 2.0 루트 허브 + USB 3.0(3.1) 루트 허브
- Genesys Logic USB 허브, SD 카드 리더 (`05e3:0749`)
- 키보드: ABKO K516 (`258a:002a`)
- 마우스: Pixart Optical Mouse (`093a:2510`)
- USB 시리얼 장치(`ttyUSB*`/`ttyACM*`): 조회 시점에 연결 없음 (로봇 통신 시 USB-CAN 어댑터가 여기에 연결됨)

---

## 6. 소프트웨어 환경

### 6.1 운영체제 / 커널
| 항목 | 값 |
|------|-----|
| 배포판 | Ubuntu 22.04.5 LTS (Jammy Jellyfish) |
| 아키텍처 | x86-64 |
| 커널 | `6.18.19-rt-x64v3-xanmod1` |
| 커널 특성 | **PREEMPT_RT 실시간 패치 + XanMod** (`x64v3` 최적화 빌드) |
| 세션 | Wayland |
| 호스트명 | `laba-desktop` |

> 실시간(PREEMPT_RT) 커널은 로봇 저수준 제어 루프의 지터(jitter)를 줄이기 위한 선택으로, 이 기기의 핵심 구성 요소입니다.

### 6.2 미들웨어 / 런타임
| 항목 | 버전 |
|------|------|
| ROS 2 | Humble (`/opt/ros/humble`) |
| Python | 3.10.12 (시스템, `/usr/bin/python3`) |
| GCC | 11.4.0 |
| CMake | 3.22.1 |
| Docker | 미설치 |

### 6.3 주요 Python 패키지 (로봇 관련)
| 패키지 | 버전 | 용도 |
|--------|------|------|
| `mujoco` | 3.6.0 | 물리 시뮬레이션 (sim-to-sim) |
| `torch` | 2.11.0+cpu | **CPU 전용** PyTorch 빌드 |
| `onnxruntime` | 1.23.2 | 정책(policy) 추론 |
| `numpy` | 2.2.6 | 수치 연산 |
| `scipy` | 1.8.0 | 수치 연산 |
| `python-can` | 4.6.1 | CAN 버스 통신 |
| `pyserial` | 3.5 | 시리얼 통신 |
| `cc.serializer` | 2024.8.17 | 데이터 직렬화 |

### 6.4 CAN 도구
- `can-utils` 설치됨 (`candump`, `cansend` 사용 가능)
- 조회 시점에 활성화된 CAN 인터페이스는 없음 (로봇 연결 시 SocketCAN 인터페이스가 활성화됨)

### 6.5 프로젝트 환경
- 저수준 제어 코드: `nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/`
- 브리지 서비스: `nuc/bhl/systemd/hylion-bridge.service` (systemd 유닛)
- 의존성: `requirements.txt` — `pyserial`, `python-can`, `cc.udp`, `onnxruntime`, `inputs`, `pynput`, `tables`

---

## 7. 요약 / 참고사항

1. **정확한 제품명은 시스템상 식별 불가** — OEM이 DMI를 비워둔 화이트박스 기기. 실제 모델명은 기기 라벨/구매처로 확인 필요.
2. **CPU/GPU는 저전력 내장형(Intel N95)** — 외장 GPU·CUDA 없음. ML 추론은 CPU(ONNX/Torch-CPU) 기반.
3. **실시간 커널(PREEMPT_RT)** 사용 — 로봇 제어 지터 최소화 목적.
4. 더 상세한 메모리 타입·시리얼 번호 등은 root 권한으로 아래 명령 실행 시 확보 가능:
   ```bash
   sudo dmidecode -t system -t baseboard -t memory
   sudo lshw -short
   ```
