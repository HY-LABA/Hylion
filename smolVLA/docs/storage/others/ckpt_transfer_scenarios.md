# ckpt 전송 시나리오 — 4 케이스 분류 및 사용자 결정 가이드

> 작성일: 2026-05-01
> 출처: 04_infra_setup 마일스톤 TODO-T2
> 목적: DGX 학습 체크포인트 → 시연장 Orin 전송 경로의 네트워크 조건별 4개 케이스를 정의하고,
>       사용자가 시연장 환경 확인 후 적절한 경로를 선택할 수 있도록 가이드를 제공한다.
> 참고 스크립트:
>   - scripts/sync_ckpt_dgx_to_orin.sh          (케이스 1·2 — 기존 스크립트)
>   - ~~scripts/sync_ckpt_dgx_to_datacollector.sh~~  (케이스 3 — **legacy 이관 완료 L2**)
> 정정 (2026-05-02): 06_dgx_absorbs_datacollector 결정으로 DataCollector 노드 운영 종료.
>       케이스 3 (DataCollector 경유) 는 더 이상 사용되지 않음. 역사적 결정으로 본문 보존.
>       sync_ckpt_dgx_to_datacollector.sh → legacy 이관: docs/storage/legacy/02_datacollector_separate_node/scripts_sync_ckpt_dgx_to_datacollector.sh
>       현재 유효 케이스: 케이스 1·2 (sync_ckpt_dgx_to_orin.sh), 케이스 4 (USB 드라이브).

---

## 배경 — 시연장 분리 아키텍처

04 마일스톤에서 4-노드 분리 아키텍처가 공식화되었다.

```
DGX (연구실)
    │
    │ DGX → devPC → Orin (기존 sync_ckpt_dgx_to_orin.sh — 케이스 1·2)
    │
    └─ 케이스 3: 시연장 Orin 격리 시 DataCollector 경유 우회
              DGX → devPC → DataCollector → Orin (수동 or USB)
```

시연장 Orin 이 devPC·DGX 와 동일 광역 네트워크에 있으면 기존 2-hop 스크립트가 그대로 동작한다.
시연장 WiFi 격리 또는 다른 서브넷인 경우 우회가 필요하다.

---

## 케이스 분류

### 케이스 1 — 동일 광역 네트워크

**조건**: 시연장 Orin 이 인터넷 접근 가능 + devPC·DGX 와 동일 학교 WiFi 서브넷 (172.16.x.x 대역 등)

**증상 (확인 방법)**:
```bash
# devPC 에서 Orin 에 직접 SSH 가능하면 케이스 1
ssh orin "hostname"
```

**전송 방법**: 기존 스크립트 직접 사용 — IP 변경 시 `~/.ssh/config` HostName 만 갱신.
```bash
bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh
```

**적합 환경**: 연구실 내 모든 장비가 같은 WiFi 대역에 있을 때.

---

### 케이스 2 — 다른 서브넷, 인터넷 가능

**조건**: 시연장 Orin 이 인터넷 접근 가능 + devPC·DGX 와 다른 서브넷
         (예: 시연장은 별도 공유기, 연구실은 학교 WiFi — 단, 외부 인터넷은 모두 가능)

**증상 (확인 방법)**:
```bash
# devPC 에서 Orin SSH 단절 → Orin 에서 인터넷 ping 은 가능
# Orin 에서 테스트:
ping -c3 8.8.8.8   # 성공이면 인터넷 가능
```

**전송 방법**: devPC 가 공개 IP 또는 포트포워딩을 통해 Orin 에 접근 가능하면 기존 스크립트 동작.
Orin 측 SSH 접근 불가 시 → 케이스 3 으로 전환.

```bash
# 먼저 devPC → Orin SSH 접속 시도
ssh orin "hostname"   # 성공이면 기존 스크립트 사용 가능
bash smolVLA/scripts/sync_ckpt_dgx_to_orin.sh
```

---

### 케이스 3 — 시연장 Orin 인터넷 격리 (DataCollector 경유 우회) — *무효화 (2026-05-02)*

<!-- 정정: DataCollector 노드 운영 종료 (06 결정). 케이스 3 사용 불가. 역사적 보존. -->

**조건**: 시연장 Orin 이 외부 인터넷 접근 불가 또는 devPC 에서 Orin SSH 단절.
         DataCollector 는 시연장 WiFi 에 있어 Orin 과 동일 서브넷 접근 가능.
         **→ 06 결정: DataCollector 운영 종료. 케이스 3 사용 불가. DGX 가 시연장 직접 이동하는 방식으로 전환.**

**증상 (확인 방법)**:
```bash
# devPC 에서 Orin SSH 불가
ssh orin "hostname"   # 실패

# DataCollector 에서 Orin SSH 는 가능 (동일 서브넷)
ssh datacollector "ssh laba@<ORIN_IP> hostname"   # 성공
```

**전송 방법 (2단계)**:

1단계 — devPC 에서 DGX → DataCollector 전송:
```bash
bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --run <run_name> --step <step_id>
# 또는 dry-run 확인 후
bash smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run
```

2단계 — DataCollector 에서 Orin 으로 수동 전송:
```bash
ssh datacollector
# DataCollector 에서 실행:
ORIN_IP=<시연장 Orin IP>
RUN=<run_name>
STEP=<step_id>
rsync -avz --delete \
    /home/laba/smolvla/ckpt_transfer/${RUN}/${STEP}/ \
    laba@${ORIN_IP}:/home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}/
```

DataCollector → Orin SSH 사전 조건:
```bash
# DataCollector 에서 Orin 에 SSH 키 배포 (최초 1회)
ssh-copy-id -i ~/.ssh/id_ed25519.pub laba@<ORIN_IP>
```

**적합 환경**: 시연장 공유기가 외부 접근 차단 + DataCollector 가 Orin 과 동일 서브넷.

**DataCollector 용량 고려**:
- DataCollector 의 `/home/laba/smolvla/ckpt_transfer/` 는 임시 저장 공간.
- Orin 전송 완료 후 불필요 파일 정리 권장:
  ```bash
  ssh datacollector "rm -rf /home/laba/smolvla/ckpt_transfer/<run>/<step>"
  ```

---

### 케이스 4 — 완전 오프라인 (USB 드라이브)

**조건**: 시연장 Orin 인터넷 격리 + DataCollector 에서 Orin SSH 도 불가.
         (예: Orin 이 WiFi 도 없고 케이블도 연결 안 됨)

**전송 방법 (USB 드라이브 직접 복사 — 자동화 불가, 사용자 직접)**:

1. DGX 에서 USB 드라이브로 복사:
   ```bash
   ssh dgx
   # DGX 에서 USB 마운트 후:
   USB_MOUNT=/media/laba/<USB_LABEL>
   RUN=<run_name>; STEP=<step_id>
   mkdir -p ${USB_MOUNT}/smolvla_ckpt/${RUN}/${STEP}
   cp -r /home/laba/smolvla/dgx/outputs/train/${RUN}/checkpoints/${STEP}/pretrained_model/ \
         ${USB_MOUNT}/smolvla_ckpt/${RUN}/${STEP}/
   sync   # 버퍼 플러시 (USB 안전 제거 전)
   ```

2. USB 드라이브를 Orin 에 연결 후 복사:
   ```bash
   ssh orin
   # Orin 에서 USB 마운트 후:
   USB_MOUNT=/media/laba/<USB_LABEL>
   RUN=<run_name>; STEP=<step_id>
   mkdir -p /home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}
   cp -r ${USB_MOUNT}/smolvla_ckpt/${RUN}/${STEP}/ \
         /home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}/
   ```

3. Orin 에서 ckpt 무결성 확인:
   ```bash
   ls -la /home/laba/smolvla/orin/checkpoints/${RUN}/${STEP}/
   # model.safetensors 존재 확인
   ```

**적합 환경**: 네트워크 완전 격리, 비상 수동 전송 시.

---

## 사용자 결정 플로우차트

```
시연장 배치 전 확인:
    │
    ├─ devPC → Orin SSH 가능?
    │      Yes → 케이스 1 또는 2
    │             sync_ckpt_dgx_to_orin.sh 사용
    │
    └─ devPC → Orin SSH 불가?
           │
           ├─ DataCollector → Orin SSH 가능?
           │      Yes → 케이스 3
           │             sync_ckpt_dgx_to_datacollector.sh + 수동 DataCollector → Orin
           │
           └─ DataCollector → Orin SSH 도 불가?
                  Yes → 케이스 4
                         USB 드라이브 직접 복사
```

---

## 확인 체크리스트 (시연장 배치 시)

```
[ ] devPC 에서 ssh orin 접속 테스트 → 성공 시 케이스 1·2 (기존 스크립트)
[ ] 실패 시: DataCollector 에서 ssh laba@<ORIN_IP> 접속 테스트 → 성공 시 케이스 3
[ ] 케이스 3 확정 시: DataCollector 에 SSH 키 배포 확인 (ssh-copy-id)
[ ] 케이스 3 확정 시: sync_ckpt_dgx_to_datacollector.sh --dry-run 으로 사전 검증
[ ] 케이스 4 (USB) 시: USB 드라이브 사전 준비 + 마운트 경로 확인
```

---

## 잔여 리스크

| 항목 | 설명 | 대응 |
|---|---|---|
| 시연장 Orin 인터넷 가용성 미확인 | 사용자가 시연장 배치 전 실제 확인 필요 | 본 문서의 체크리스트 참조 |
| DataCollector SSH 키 미배포 | 케이스 3 시 DataCollector → Orin SSH 먼저 설정 필요 | 시연장 배치 checklist 에 포함 |
| DataCollector 임시 ckpt 용량 | 대용량 ckpt 쌓이면 DataCollector 디스크 부족 | 전송 완료 후 ckpt_transfer/ 정리 |
| DHCP 변동 | 시연장 Orin IP 변경 시 DataCollector 측 rsync 대상 IP 갱신 필요 | 매 시연 전 ip addr 확인 |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 04 TODO-T2 산출물. 4개 케이스 정의, 사용자 결정 플로우차트, 체크리스트, 잔여 리스크 명시. |
