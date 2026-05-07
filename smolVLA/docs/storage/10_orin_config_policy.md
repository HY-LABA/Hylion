# orin/config/ — git 추적 정책 명문화

> 작성일: 2026-05-03
> 출처: `07_e2e_pilot_and_cleanup` TODO-W4 (04 BACKLOG #3 흡수)
> 목적: `orin/config/ports.json` · `cameras.json` 의 git 추적 vs gitignore 정책 결정을 명문화하고, 환경별 충돌 회피 방법을 기록.

---

## 1. 결정

**git 추적 유지 (결정 (a))**

- 결정 기준: 07_e2e_pilot_and_cleanup Phase 1 사용자 위임 #3 → default (a)
- 날짜: 2026-05-03
- `.gitignore` 변경 X (Category B 회피)

---

## 2. 현재 추적 파일

`git ls-files orin/config/` 결과 (2026-05-03 기준):

| 파일 | 내용 |
|---|---|
| `orin/config/README.md` | 이 디렉터리 설명·재생성 절차 |
| `orin/config/ports.json` | SO-ARM follower/leader 포트 캐시 |
| `orin/config/cameras.json` | 카메라 슬롯별 인덱스·flip 캐시 |

### 파일 현재값 (2026-05-03 시점)

`ports.json`:
```json
{
  "follower_port": null,
  "leader_port": null
}
```

`cameras.json`:
```json
{
  "top": {"index": null, "flip": false},
  "wrist": {"index": null, "flip": false}
}
```

현재값은 **placeholder** (`null`). 시연장 SO-ARM·카메라 직결 셋업 후 `orin/tests/check_hardware.sh --mode first-time` 실행 시 실제값으로 갱신될 예정 (TODO-G1 구현 예정, `orin/config/README.md` 참조).

변경 이력: `git log --oneline orin/config/ports.json orin/config/cameras.json` — `b028684 update` (1건, 초기 커밋).

---

## 3. 결정 사유

(a) git 추적 유지가 적합한 이유:

1. **시연장 셋업 후 안정적**: SO-ARM 포트·카메라 인덱스는 시연장에서 한 번 셋업하면 이후 고정됨. 매 실행마다 재발견할 필요 없어 git 추적 + 캐시 보존이 운영에 편리.
2. **reference 역할**: placeholder null 값이 git 에 남아 있어도 다른 인스턴스 (devPC·팀원) 가 구조(스키마)를 알 수 있음. 실제 환경값은 시연장 Orin 에서만 의미 있음.
3. **사용자 결정 (D)**: 시연장 이동 후 SO-ARM·카메라 직결 환경 고정 — 사용자가 환경별 override 관리를 직접 할 수 있음을 전제로 결정.
4. **Category B 회피**: `.gitignore` 패턴 변경은 Category B (자동 재시도 X 영역). 현 사이클 내에서 불필요한 Category B 개입을 최소화.

---

## 4. 알려진 제한·충돌 가능성

| 상황 | 영향 | 대처 |
|---|---|---|
| devPC 에서 null 값 git 추적 상태에서 Orin 실값으로 git pull | Orin 실값이 devPC 의 null 로 덮어써짐 가능성 | Orin 에서 작업 중일 때 devPC 는 해당 파일 pull 자제. 또는 아래 git stash 방법 사용 |
| 다른 팀원 환경 (Orin 포트 인덱스 다름) | ports.json·cameras.json 값 충돌 | `git stash` 또는 환경별 override (§5) 활용 |
| 시연장 변경 (USB 포트 재배치·카메라 교체) | 기존 git 추적 값과 실 환경 불일치 | §6 갱신 절차 따라 git commit 으로 갱신 |

---

## 5. 환경별 override 방법 (git 추적 유지하면서 로컬 변경 보존)

### 5-1. git stash 방법 (임시)

```bash
# 로컬 환경값 보존하면서 pull 받을 때
git stash -- orin/config/ports.json orin/config/cameras.json
git pull
git stash pop
# 충돌 시 수동 병합: 로컬 환경값 우선
```

### 5-2. local.json 패턴 (차후 도입 후보 — 현재 미적용)

환경별 충돌이 빈발하면 다음 패턴 도입 검토:
- `orin/config/ports.json` → 공통 placeholder (git 추적)
- `orin/config/ports.local.json` → 실 환경값 (`.gitignore` 추가, Category B 동의 필요)
- 운영 스크립트가 `*.local.json` 우선 로드, 없으면 `*.json` fallback

도입 트리거: 동일 파일에 대한 git conflict 2회 이상 발생 시 또는 팀원 증가 시 사용자와 결정.

---

## 6. 시연장 환경 변경 시 갱신 절차

시연장 셋업 후 또는 환경 변경(포트 재배치·카메라 교체) 발생 시:

```bash
# 1. check_hardware.sh 실행으로 자동 갱신 (TODO-G1 구현 후)
bash orin/tests/check_hardware.sh --mode first-time --output-config orin/config/

# 2. 변경 확인 후 commit
git diff orin/config/
git add orin/config/ports.json orin/config/cameras.json
git commit -m "config(orin): 시연장 셋업 후 ports/cameras 갱신 — <날짜> <환경 메모>"

# 3. 필요 시 본 문서 §7 변경 이력 갱신
```

---

## 7. 변경 이력

| 날짜 | 변경 내용 | 출처 |
|---|---|---|
| 2026-04-30 (b028684) | ports.json·cameras.json placeholder null 초기 커밋 | 04_infra_setup TODO-O1 |
| 2026-05-03 | git 추적 유지 정책 명문화 (본 문서 신규) | 07_e2e_pilot_and_cleanup TODO-W4 |

---

## 8. 차후 결정 후보 (낮음)

- `*.example.json` 템플릿 + local override 분리 — §5-2 참조. 사용자 환경 충돌 빈발 시 트리거.
- `check_hardware.sh --mode first-time` 구현 (TODO-G1) 완료 시 본 문서 §6 갱신 방법 확정.

---

## 참고

- `orin/config/README.md` — 이 디렉터리 자산 설명·재생성 방법
- `docs/work_flow/specs/BACKLOG.md` § 04_infra_setup #3 — 본 문서 원 출처
- `docs/work_flow/specs/07_e2e_pilot_and_cleanup.md` § TODO-W4 — 본 작업 출처
