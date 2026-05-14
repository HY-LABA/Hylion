# Dev Network 설정 (WiFi SSH)

> 작성일: 2026-04-21  
> 업데이트: 2026-05-13 (eduroam 추가 + DataCollector 제거 — 06_dgx_absorbs_datacollector 흡수 반영)
> 목적: devPC ↔ Jetson Orin, devPC ↔ DGX Spark 간 WiFi SSH 연결 설정 기록

---

## 1) 장비 개요

| 장비 | 역할 | OS | 호스트명 | 유저명 |
|---|---|---|---|---|
| devPC | 코드 정리/문서화/배포 관리 | Ubuntu 22.04 | `babogaeguri-950QED` | `babogaeguri` |
| Jetson Orin Nano Super | 실행/검증 (SO-ARM 연결) | Ubuntu 22.04 (L4T R36.5.0) | `ubuntu` | `laba` |
| DGX Spark | 학습/파인튜닝 + 데이터 수집 (06 사이클 datacollector 흡수) | Ubuntu | `spark-8434` | `laba` |

---

## 2) 네트워크 정보 수집

| 장비 | WiFi IP | 서브넷 게이트웨이 | 비고 |
|---|---|---|---|
| devPC | 동적 | (네트워크별 변동) | DHCP, 변동 있음 |
| Jetson Orin | `172.16.137.232` (HY-WiFi) | `172.16.137.254` | DHCP, 변동 있음. 2026-04-29 확인. **eduroam 미사용** |
| DGX Spark | eduroam `172.16.142.85` / HY-WiFi `172.16.133.237` / LAN `192.168.0.7` | 네트워크별 변동 / LAN `192.168.0.1` | DHCP, 변동 있음. 2026-05-13 eduroam 추가 확인. 2026-05-11 HY-WiFi 재확인 |

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

---

## 4) SSH 키 기반 인증 설정 (패스워드 없이 접속)

- devPC에서 ed25519 키 생성 후 각 장비에 공개키 배포
- 기본 키 경로: `~/.ssh/id_ed25519`

---

## 5) SSH Config 설정 (`~/.ssh/config`)

devPC의 `~/.ssh/config`에 Orin / DGX Spark 항목 추가:

| 항목 | Orin | DGX Spark |
|---|---|---|
| Host alias | `orin` | `dgx` |
| HostName | Orin의 현재 IP 직접 기재 | 현재 연결 네트워크의 IP 직접 기재 |
| User | `laba` | `laba` |
| Port | `22` | `22` |
| IdentityFile | `~/.ssh/id_ed25519` | `~/.ssh/id_ed25519` |
| ServerAliveInterval | `30` | `30` |
| ServerAliveCountMax | `5` | `5` |

> mDNS 불가 환경이므로 HostName에 IP를 직접 기재한다. IP 변경 시 수동 업데이트 필요.  
> `ServerAliveInterval` / `ServerAliveCountMax`: WiFi 환경에서 idle 세션 끊김 방지  
> DGX 네트워크별 IP 분기는 `scripts/dev-connect.sh` 가 직접 처리 (HY-WiFi / eduroam 별 IP 박혀 있음 — §6 참조)

---

## 6) VS Code Remote SSH 설정

1. VS Code 확장 설치: `Remote - SSH` (`ms-vscode-remote.remote-ssh`)
2. `F1` → `Remote-SSH: Connect to Host...`
3. `~/.ssh/config`에 등록된 `orin` 또는 `dgx` 선택
4. 처음 연결 시 플랫폼 선택: `Linux`

### 권장 워크스페이스 경로

| 장비 | Remote 워크스페이스 경로 |
|---|---|
| Orin | `/home/laba` |
| DGX Spark | `/home/laba` |

### `scripts/dev-connect.sh` — 네트워크 분기 진입

`~/.ssh/config` alias 우회로 IP 를 직접 지정해 VS Code Remote 세션을 여는 헬퍼. 두 위치 인자.

```bash
./scripts/dev-connect.sh orin            # Orin 만
./scripts/dev-connect.sh dgx  hy         # DGX 만, HY-WiFi IP
./scripts/dev-connect.sh dgx  edu        # DGX 만, eduroam IP
./scripts/dev-connect.sh both hy         # Orin + DGX(HY-WiFi)
./scripts/dev-connect.sh both edu        # Orin + DGX(eduroam)
```

스크립트 상단 3변수(`ORIN_IP`, `DGX_IP_HY`, `DGX_IP_EDU`) 가 IP 를 보유 — DHCP 재할당 시 그 부분만 수정. Orin 은 eduroam 미사용이라 네트워크 인자 불필요.

---

## 7) 학교 WiFi 연결 방법 (WPA2 Enterprise)

학교 WiFi(HY-WiFi·eduroam)는 기업용 WPA2 인증을 사용하므로 일반 비밀번호 입력이 아닌 아래 설정이 필요하다.  
GUI(NetworkManager) 기준으로 설정한다.

### 7-1) HY-WiFi

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

### 7-2) eduroam (2026-05-13 추가)

| 항목 | 값 |
|---|---|
| SSID | `eduroam` |
| Wi-Fi security | WPA & WPA2 Enterprise |
| Authentication | Protected EAP (PEAP) |
| Anonymous identity | (비워둠) |
| Domain | (비워둠) |
| CA certificate | (없음), `No CA certificate is required` 체크 |
| PEAP version | Automatic |
| Inner authentication | MSCHAPv2 |
| Username | `<학교포털ID>@hanyang.ac.kr` (HY-WiFi 와 달리 **realm 필수**) |
| Password | 학교 포털 비밀번호 |

> eduroam GUI 다이얼로그 첫 진입 시 `Authentication` 이 `Tunneled TLS` 로 기본값 잡혀 있을 수 있음 → **Protected EAP (PEAP)** 로 먼저 변경해야 하부 필드 구성이 PEAP 용으로 다시 그려진다.

### 7-3) DGX Spark WiFi 운영 주의

> **DGX WiFi 활성화**: DGX Spark는 초기 WiFi 어댑터(`wlP9s9`)가 비활성화 상태이므로, GUI 연결 전 `nmcli radio wifi on`으로 활성화 필요.
>
> **DGX 라우팅 설정**: DGX는 LAN(`enP7s7`, `192.168.0.x`)과 WiFi(`wlP9s9`)가 동시에 연결되어 있으며, 기본 라우트가 LAN으로 잡혀 있어 WiFi 쪽에서 접속하면 패킷이 LAN으로 나가 통신 불가 상태가 된다. 이를 해결하기 위해 `172.16.0.0/16` 대역(학교 WiFi 장비들)만 WiFi 게이트웨이로 보내는 라우트를 추가한다. 이 설정은 **각 NetworkManager 프로파일별로 영구 저장** 되므로 HY-WiFi·eduroam 양쪽 프로파일에 각각 추가해야 한다. LAN을 통한 팀원의 SSH 접속에는 영향 없이 동시 사용 가능하다.
>
> ```bash
> nmcli connection modify HY-WiFi  +ipv4.routes "172.16.0.0/16 <hy-wifi 게이트웨이>"
> nmcli connection modify eduroam  +ipv4.routes "172.16.0.0/16 <eduroam 게이트웨이>"
> ```
>
> 게이트웨이는 각 프로파일 연결 직후 `ip route | grep default` 의 해당 인터페이스 행에서 확인.

---

## 8) 시연 체크리스트

시연장이 평소 사용 WiFi와 다를 경우 IP가 바뀔 수 있으므로 아래를 순서대로 확인한다.

- [ ] 시연장 WiFi 에 devPC·Orin·DGX 모두 연결 (Orin 은 HY-WiFi 만 지원 — eduroam 환경이면 Orin 핫스팟 별도 대응)
- [ ] Orin 에서 현재 WiFi IP 확인 (`ip addr show | grep "inet "`)
- [ ] DGX 에서 현재 WiFi IP 확인 (`ip addr show wlP9s9 | grep "inet "`)
- [ ] devPC `~/.ssh/config` 의 Orin·DGX HostName 또는 `scripts/dev-connect.sh` 상단 IP 변수 갱신
- [ ] `ssh orin` / `ssh dgx` 또는 `dev-connect.sh <target> <network>` 접속 테스트
- [ ] (장기) 학교 통신처에 Orin·DGX MAC주소 제출 → DHCP 예약 요청

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
- [x] DGX 라우팅 설정 (LAN/WiFi 동시 연결 환경에서 `172.16.0.0/16` → WiFi 라우트 추가, HY-WiFi 프로파일 nmcli 영구 저장)
- [x] devPC ↔ DGX SSH 접속 성공 확인
- [x] Orin·DGX IP 변경 시 `~/.ssh/config` HostName 업데이트 절차 숙지 (섹션 8 시연 체크리스트, 섹션 10 트러블슈팅 참고)
- [x] devPC eduroam 연결 성공 (2026-05-13, §7-2)
- [x] DGX eduroam IP 확인 (`172.16.142.85`, 2026-05-13)
- [x] `scripts/dev-connect.sh` 네트워크 분기 추가 (`hy`/`edu`, 2026-05-13)
- [ ] DGX eduroam 프로파일에 `172.16.0.0/16` WiFi 라우트 추가 (§7-3) — 미확인, 첫 SSH 시도 시 검증

---

## 10) 트러블슈팅: SSH 접속 실패 (IP 변경)

### 발생 이력

- **2026-04-22**: DGX Spark WiFi를 끊었다가 재연결하자 DHCP가 새 IP(`172.16.133.66`)를 할당 → 기존 `~/.ssh/config`의 IP(`172.16.128.93`)와 달라져 VS Code Remote SSH 및 터미널 SSH 모두 실패
- **2026-05-06**: DGX Spark 재부팅·WiFi 재연결 후 DHCP 가 새 IP(`172.16.129.180`) 할당 → 서브넷 자체가 `172.16.129.x` 로 변경. `~/.ssh/config` HostName 갱신 필요
- **2026-05-08**: DGX Spark WiFi 재할당으로 새 IP(`172.16.131.33`) → 서브넷 `172.16.131.x` 로 변경. `~/.ssh/config` HostName 갱신 완료
- **2026-05-11**: DGX Spark WiFi 재할당으로 새 IP(`172.16.133.237`) → 서브넷 `172.16.133.x` 로 변경. `~/.ssh/config` HostName 갱신 완료
- **2026-05-13**: DGX Spark 가 eduroam 으로 네트워크 전환 → 새 IP(`172.16.142.85`), 서브넷 `172.16.142.x`. devPC 도 eduroam 으로 이동 (§7-2), `scripts/dev-connect.sh` 가 네트워크별 IP 분기 흡수 (이제 `~/.ssh/config` HostName 직접 갱신 대신 dev-connect.sh 상단 변수만 갱신)

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
