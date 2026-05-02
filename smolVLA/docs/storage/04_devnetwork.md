# Dev Network 설정 (WiFi SSH)

> 작성일: 2026-04-21  
> 업데이트: 2026-05-02 (DataCollector 추가)
> 목적: devPC ↔ Jetson Orin, devPC ↔ DGX Spark, devPC ↔ DataCollector 간 WiFi SSH 연결 설정 기록

---

## 1) 장비 개요

| 장비 | 역할 | OS | 호스트명 | 유저명 |
|---|---|---|---|---|
| devPC | 코드 정리/문서화/배포 관리 | Ubuntu 22.04 | `babogaeguri-950QED` | `babogaeguri` |
| Jetson Orin Nano Super | 실행/검증 (SO-ARM 연결) | Ubuntu 22.04 (L4T R36.5.0) | `ubuntu` | `laba` |
| DGX Spark | 학습/파인튜닝 전용 | Ubuntu | `spark-8434` | `laba` |
| DataCollector | 데이터 수집 (SO-ARM teleop + lerobot-record) | Ubuntu 22.04 (kernel 6.8.0-106 HWE) | `smallgaint` | `smallgaint` |

---

## 2) 네트워크 정보 수집

| 장비 | WiFi IP (예시) | 서브넷 게이트웨이 | 비고 |
|---|---|---|---|
| devPC | 동적 | `172.16.141.254` | DHCP, 변동 있음 |
| Jetson Orin | `172.16.137.232` | `172.16.137.254` | DHCP, 변동 있음. 2026-04-29 확인 |
| DGX Spark | WiFi `172.16.133.66` / LAN `192.168.0.7` | WiFi `172.16.133.254` / LAN `192.168.0.1` | DHCP, 변동 있음. 2026-04-22 재확인 (WiFi 재연결 후 변경) |
| DataCollector | `172.16.133.102` (`wlp1s0`) | `172.16.133.254` | DHCP, 변동 있음. 2026-05-02 확인. MAC `e4:70:b8:09:4c:ed`. unattended-upgrade 후 재부팅 시 IP 변경 가능 |

> **접속 방식 결정 배경**
>
> devPC가 Orin에 접속하려면 Orin의 IP를 알아야 한다. 학교 DHCP 환경에서 이를 해결하는 방법은 세 가지이며, 각각 아래와 같은 이유로 채택/기각되었다.
>
> | 방법 | 원리 | 오늘 환경 결과 |
> |---|---|---|
> | **공유기 DHCP 예약** | Orin MAC주소에 IP 고정 배정 | 학교 공유기 접근 불가 → 기각 |
> | **mDNS (`ubuntu.local`)** | Orin이 네트워크에 자신의 hostname 브로드캐스트 → devPC가 IP 자동 파악 | devPC·Orin이 다른 서브넷에 배정되어 브로드캐스트가 닿지 않음 → 기각 |
> | **IP 직접 지정** | 현재 IP를 수동 확인 후 `~/.ssh/config`에 기재 | 현재 동작 중 → **채택** |
>
> 공유기 DHCP 예약이 가능하다면 가장 안정적이다. 학교 통신처에 Orin의 MAC주소를 제출하고 예약을 요청하는 것이 장기적으로 권장된다.
>
> 현재 학교 DHCP가 MAC 기반으로 같은 IP를 재배정하는 것으로 보이나(soft 고정), 보장되지 않으므로 연결 실패 시 IP 변경 여부를 먼저 확인한다.

---

## 3) SSH 서버 설치/활성화 확인

### Jetson Orin (확인됨)
- `openssh-server` 설치됨
- `ssh.service`: `active`, `enabled`
- `0.0.0.0:22`, `[::]:22` 리슨 확인 → 별도 설정 불필요
- `avahi-daemon`: `active`, `enabled` (단, 서브넷 분리로 mDNS 사용 불가)

### DGX Spark (확인됨)
- `openssh-server` 설치됨
- `ssh.service`: `active`, `running` (TriggeredBy: ssh.socket)
- `0.0.0.0:22`, `[::]:22` 리슨 확인 → 별도 설정 불필요
- `avahi-daemon`: 미확인 (mDNS 사용 계획 없으므로 불필요)

### DataCollector (확인됨, 2026-05-02)
- `openssh-server 1:8.9p1-3ubuntu0.15` 설치 (sudo apt install — unattended-upgrade 락 해제 후)
- `ssh.service`: `active`, `enabled` (자동 시작)
- `0.0.0.0:22`, `[::]:22` 리슨 확인 (`ss -tlnp | grep :22`)
- 방화벽 (`ufw`): `inactive` — 별도 SSH 허용 규칙 불필요
- ED25519 host key fingerprint: `SHA256:OdTLLyHp0rxq9OrmDHjy9y8/On/GuKrWNuMVnhKs1R4`

---

## 4) SSH 키 기반 인증 설정 (패스워드 없이 접속)

- devPC에서 ed25519 키 생성 후 각 장비에 공개키 배포
- 기본 키 경로: `~/.ssh/id_ed25519`

---

## 5) SSH Config 설정 (`~/.ssh/config`)

devPC의 `~/.ssh/config`에 Orin / DGX Spark / DataCollector 항목 추가:

| 항목 | Orin | DGX Spark | DataCollector |
|---|---|---|---|
| Host alias | `orin` | `dgx` | `datacollector` |
| HostName | Orin의 현재 IP 직접 기재 | 확인 후 기재 | `172.16.133.102` (확인 후 기재) |
| User | `laba` | `laba` | `smallgaint` |
| Port | `22` | `22` | `22` |
| IdentityFile | `~/.ssh/id_ed25519` | `~/.ssh/id_ed25519` | `~/.ssh/id_ed25519` |
| ServerAliveInterval | `30` | `30` | `30` |
| ServerAliveCountMax | `5` | `5` | `5` |

> mDNS 불가 환경이므로 HostName에 IP를 직접 기재한다. IP 변경 시 수동 업데이트 필요.  
> `ServerAliveInterval` / `ServerAliveCountMax`: WiFi 환경에서 idle 세션 끊김 방지

---

## 6) VS Code Remote SSH 설정

1. VS Code 확장 설치: `Remote - SSH` (`ms-vscode-remote.remote-ssh`)
2. `F1` → `Remote-SSH: Connect to Host...`
3. `~/.ssh/config`에 등록된 `orin` 또는 `dgx` 선택
4. 처음 연결 시 플랫폼 선택: `Linux`

### 권장 워크스페이스 경로

| 장비 | Remote 워크스페이스 경로 |
|---|---|
| Orin | `/home/laba` (확정 후 업데이트) |
| DGX Spark | `/home/laba` (확정 후 업데이트) |
| DataCollector | `/home/smallgaint` (확정) |

`scripts/dev-connect.sh` 호출 시 3 노드 VS Code Remote 동시 진입.

---

## 7) HY-WiFi 연결 방법 (WPA2 Enterprise)

학교 WiFi(HY-WiFi)는 기업용 WPA2 인증을 사용하므로 일반 비밀번호 입력이 아닌 아래 설정이 필요하다.  
GUI(NetworkManager) 기준으로 설정한다.

| 항목 | 값 |
|---|---|
| SSID | `HY-WiFi` |
| Wi-Fi security | 기업용 WPA 또는 WPA2 |
| Authentication | 보호되는 EAP (PEAP) |
| Anonymous identity | (비워둠) |
| CA certificate | (없음), CA 인증서 불필요 체크 |
| PEAP version | 자동 |
| Inner authentication | MSCHAPv2 |
| Username | 학교 포털 아이디 |
| Password | 학교 포털 비밀번호 |

> DGX Spark는 초기 WiFi 어댑터(`wlP9s9`)가 비활성화 상태이므로, GUI 연결 전 `nmcli radio wifi on`으로 활성화 필요.
>
> **DGX 라우팅 설정**: DGX는 LAN(`enP7s7`, `192.168.0.x`)과 WiFi(`wlP9s9`, `172.16.128.x`)가 동시에 연결되어 있으며, 기본 라우트가 LAN으로 잡혀 있어 WiFi 쪽에서 접속하면 패킷이 LAN으로 나가 통신 불가 상태가 된다. 이를 해결하기 위해 `172.16.0.0/16` 대역(학교 WiFi 장비들)만 WiFi 게이트웨이로 보내는 라우트를 추가하였다. 이 설정은 HY-WiFi 연결 프로파일에 영구 저장되어 있으므로 재연결 시에도 자동 적용된다. LAN을 통한 팀원의 SSH 접속에는 영향 없이 동시 사용 가능하다.

---

## 8) 시연 체크리스트

시연장이 평소 사용 WiFi와 다를 경우 IP가 바뀔 수 있으므로 아래를 순서대로 확인한다.

- [ ] 시연장 WiFi에 devPC·Orin·DGX·DataCollector 모두 연결
- [ ] Orin에서 현재 WiFi IP 확인
- [ ] DGX에서 현재 WiFi IP 확인
- [ ] DataCollector에서 현재 WiFi IP 확인 (`ip addr show wlp1s0 | grep inet`)
- [ ] devPC `~/.ssh/config`의 Orin·DGX·DataCollector HostName을 확인된 IP로 업데이트
- [ ] `ssh orin` / `ssh dgx` / `ssh datacollector` 접속 테스트
- [ ] (장기) 학교 통신처에 Orin·DGX·DataCollector MAC주소 제출 → DHCP 예약 요청 (DataCollector MAC: `e4:70:b8:09:4c:ed`)

---

## 9) 확인 필요 항목

- [x] Orin 호스트명 확인 → `ubuntu`, 유저명 `laba`
- [x] devPC `avahi-daemon` 동작 확인 (active)
- [x] Orin `avahi-daemon` 동작 확인 (active)
- [x] devPC ↔ Orin SSH 접속 성공 확인 (IP 직접 방식, VS Code Remote-SSH)
- [x] SSH 키 기반 인증 설정 (ed25519 키 생성 후 Orin·DGX 배포 완료, 비밀번호 없이 접속 확인)
- [x] `~/.ssh/config`에 `ServerAliveInterval 30` / `ServerAliveCountMax 5` 추가 완료
- [x] DGX Spark 호스트명(`spark-8434`), 유저명(`laba`) 확인
- [x] DGX Spark WiFi IP 확인(`172.16.133.66`) 후 `~/.ssh/config` HostName 업데이트 (2026-04-22 WiFi 재연결로 변경됨)
- [x] DGX 라우팅 설정 (LAN/WiFi 동시 연결 환경에서 `172.16.0.0/16` → WiFi 라우트 추가, nmcli 영구 저장)
- [x] devPC ↔ DGX SSH 접속 성공 확인
- [x] Orin·DGX IP 변경 시 `~/.ssh/config` HostName 업데이트 절차 숙지 (섹션 8 시연 체크리스트, 섹션 10 트러블슈팅 참고)
- [x] DataCollector 호스트명·유저명 확인 (`smallgaint` / `smallgaint`, 2026-05-02)
- [x] DataCollector WiFi IP 확인 (`172.16.133.102`, 2026-05-02)
- [x] DataCollector openssh-server 설치·active·enabled (2026-05-02)
- [x] devPC `~/.ssh/config` 에 datacollector 항목 추가 (2026-05-02)
- [x] devPC ↔ DataCollector SSH 키 기반 접속 성공 (2026-05-02)
- [x] `scripts/dev-connect.sh` 에 datacollector 항목 추가 (2026-05-02)

---

## 10) 트러블슈팅: SSH 접속 실패 (IP 변경)

### 발생 이력

- **2026-04-22**: DGX Spark WiFi를 끊었다가 재연결하자 DHCP가 새 IP(`172.16.133.66`)를 할당 → 기존 `~/.ssh/config`의 IP(`172.16.128.93`)와 달라져 VS Code Remote SSH 및 터미널 SSH 모두 실패

### 증상

- VS Code: `Could not establish connection to "dgx"`
- 터미널: `ssh: connect to host ... port 22: Connection refused`

### 원인

학교 DHCP 환경에서 WiFi를 재연결하면 새로운 IP가 할당될 수 있음. `~/.ssh/config`의 HostName은 자동 갱신되지 않으므로 수동 확인 필요.

### 진단 순서

1. devPC에서 SSH 접속 시도 → Connection refused 또는 timeout 발생
2. DGX에 물리적으로 접근하여 현재 IP 확인:
   ```
   ip addr show | grep "inet "
   ```
   → `wlp9s9` 항목의 IP가 현재 WiFi IP
3. devPC의 `~/.ssh/config` 확인:
   ```
   cat ~/.ssh/config
   ```

### 해결 방법

devPC의 `~/.ssh/config`에서 dgx의 HostName을 DGX에서 확인한 현재 IP로 수정:

```
Host dgx
    HostName <새 IP>
    ...
```

수정 후 `ssh dgx`로 접속 테스트.

### 참고

- ping 실패(100% loss)가 발생해도 DGX 자체가 꺼진 게 아닐 수 있음 — 방화벽이 ICMP를 차단하는 경우도 있으므로 SSH 직접 시도 및 물리적 확인이 우선
- SSH 서비스 상태는 DGX에서 `systemctl status ssh`로 확인 가능

### DataCollector 시연장 배치 시 DHCP 리스크 (흡수: 09_datacollector_setup.md §4-1)

DataCollector 는 시연장 WiFi 에 의존하므로 DGX 와 동일한 DHCP 변동 리스크가 존재.

| 상황 | 증상 | 대처 |
|---|---|---|
| 시연장 WiFi 재연결 | DataCollector IP 변경 → devPC SSH 단절 | DataCollector 에서 `ip addr show wlp1s0` 확인 후 `~/.ssh/config` HostName 업데이트 |
| 평소와 다른 시연장 WiFi | IP 대역 변경 가능 | SSH 접속 전 IP 재확인 필수 (§8 시연 체크리스트 참조) |
| unattended-upgrade 후 재부팅 | IP 변경 가능 (2026-05-02 사례) | 재부팅 후 `ip addr show wlp1s0 | grep inet` 로 IP 재확인 |

**DataCollector DHCP 예약 권장**: MAC 주소 `e4:70:b8:09:4c:ed` 기준으로 시연장 공유기 관리자에게 고정 IP 예약 요청 (장기). 현재는 IP 직접 기재 방식 (soft 고정 기대) 사용 — 연결 실패 시 IP 변경 여부 먼저 확인.

---

## 11) 학교 WiFi 차단 endpoint 목록 (2026-05-02 추가)

학교 WiFi (HY-WiFi) 환경에서 일부 외부 endpoint 가 timeout / connection refused 로 차단되거나 매우 느린 응답을 보임. 셋업·deploy 작업 시 사전 인지 후 다른 네트워크 (개인 핫스팟·집 WiFi) 로 우회 권장.

### 11-1) 확인된 차단·느림 endpoint

| Endpoint | 용도 | 학교 WiFi 동작 | 우회 |
|---|---|---|---|
| `launchpad.net` (Ubuntu PPA API) | `add-apt-repository ppa:...` 의 메타데이터 fetch (deadsnakes 등) | **TimeoutError [Errno 110]** 확인 (2026-05-02 datacollector setup) | 핫스팟·집 WiFi / `add-apt-repository --no-update` 후 직접 `/etc/apt/sources.list.d/` 수정 / `uv` 같은 standalone Python 도구 |
| `keyserver.ubuntu.com` (PPA GPG key) | PPA 추가 시 GPG 키 fetch | launchpad 와 같은 인프라 — 차단 가능성 | 동일 우회 |

### 11-2) 일반적으로 정상 동작 endpoint (참고)

| Endpoint | 용도 | 학교 WiFi 동작 |
|---|---|---|
| `pypi.org`·`files.pythonhosted.org` | pip install (~700MB torch wheel 등) | 정상 (느릴 수 있음) |
| `huggingface.co` | HF Hub model·dataset 다운로드 | 일반적으로 정상 (단 시연장 등 일부 환경에서 격리 필요 시 §6 demo_site_mirroring 참조) |
| `github.com`·`*.githubusercontent.com` | git clone·raw 파일 | 정상 |
| `astral.sh` (uv 설치 스크립트) | `curl https://astral.sh/uv/install.sh | sh` | 일반적 정상 |
| `kr.archive.ubuntu.com` (Ubuntu 공식 mirror) | `apt update`·`apt install` | 정상 (학교 WiFi 가 한국 mirror 사용 시) |

### 11-3) 차단 발견 시 대응 절차

1. 어떤 작업 단계에서 timeout 발생했는지 본 문서 §11-1 표에 기록
2. 우회 방법 시도 (다른 네트워크 또는 standalone 도구)
3. 우회 불가 시 BACKLOG 이관 + 다른 환경에서 처리 (시연 전·시연 후 등)
4. 향후 동일 endpoint 재발 시 본 표 먼저 확인 → 시간 소비 회피

### 11-4) 본 사이클 (05_interactive_cli) 학습 신호

`add-apt-repository -y ppa:deadsnakes/ppa` 시도 시 launchpad.net Connection timeout (2026-05-02 datacollector). 이로 인해 Python 3.12 셋업 차단 → BACKLOG #11 (다음 사이클 처리). **다음 사이클 진입 시 다른 네트워크 (개인 핫스팟) 사용 또는 `uv` standalone Python 우회 권장**.
