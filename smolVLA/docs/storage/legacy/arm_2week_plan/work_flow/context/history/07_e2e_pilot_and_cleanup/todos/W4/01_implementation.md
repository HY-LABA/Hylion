# TODO-W4 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

04 BACKLOG #3 — `orin/config/ports.json`·`cameras.json` 의 git 추적 정책 결정·명문화.
사용자 위임 결정 (a) "git 추적 유지 + 정책 문서 신규" 적용. `.gitignore` 변경 X.

---

## Step 1 — 현 상태 확인 결과

### orin/config/ 파일 목록

```
cameras.json
ports.json
README.md
```

### git 추적 여부 (`git ls-files orin/config/`)

```
orin/config/README.md
orin/config/cameras.json
orin/config/ports.json
```

세 파일 모두 git 추적 중.

### 변경 이력 (`git log --oneline orin/config/`)

```
b028684 update
```

커밋 1건 — 초기 placeholder null 커밋 (04_infra_setup 시점).

### 파일 현재값

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

현재값은 placeholder (`null`). `orin/config/README.md` 에 기술된 대로 `orin/tests/check_hardware.sh --mode first-time` 실행 시 실값으로 갱신 예정 (TODO-G1 미구현).

---

## Step 2 — 정책 결정 근거

### (a) git 추적 유지 결정 사유

1. 시연장 셋업 후 포트·카메라 인덱스는 안정적 — 매 실행마다 재발견 불필요, 캐시 목적 달성
2. placeholder null 이어도 스키마 참조 가치 (다른 인스턴스에 구조 전달)
3. 사용자 결정 (D — 시연장 이동 후 SO-ARM·카메라 직결 환경 고정) 과 정합
4. Category B (.gitignore 변경) 개입 회피 — 불필요한 복잡도 X

### (a) 의 한계 (명문화)

- 별 인스턴스 환경 (devPC·다른 사용자) 에서 null vs 실값 충돌 가능
- 시연장 환경 변경 시 (USB 포트 재배치·카메라 교체) git commit 필요
- git stash 또는 local override 패턴으로 완화 가능

---

## Step 3 — 신규 파일 작성

`docs/storage/15_orin_config_policy.md` 신규 작성 완료.

### 포함 섹션

| 섹션 | 내용 |
|---|---|
| §1 결정 | git 추적 유지 (a), 날짜, .gitignore 변경 X |
| §2 현재 추적 파일 | ls·git ls-files 결과 + 파일 현재값 (null placeholder) |
| §3 결정 사유 | 4가지 사유 |
| §4 알려진 제한·충돌 가능성 | 3가지 상황·영향·대처 표 |
| §5 환경별 override 방법 | git stash 방법 + local.json 패턴 (차후 후보) |
| §6 시연장 환경 변경 시 갱신 절차 | check_hardware.sh + git commit 흐름 |
| §7 변경 이력 | 초기 커밋 + 본 문서 신규 |
| §8 차후 결정 후보 | local.json 패턴 트리거 조건 |

---

## Step 4 — 04 BACKLOG #3 마킹

`docs/work_flow/specs/BACKLOG.md` 의 `[04_infra_setup] #3` 항목:

**이전**: `미완`

**갱신 후**: `완료 (07 W4 정책 문서 신규 — docs/storage/15_orin_config_policy.md, 2026-05-03)`

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/15_orin_config_policy.md` | 신규 | orin/config/ git 추적 정책 명문화 |
| `docs/work_flow/specs/BACKLOG.md` | M | 04 #3 → 완료 마킹 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `.gitignore` 변경 X ✓ (Category B 회피)
- Coupled File Rule: `orin/lerobot/`·`pyproject.toml`·`setup_env.sh` 미변경 — coupled file 갱신 불요 ✓
- 레퍼런스 활용: 본 todo 는 정책 문서 신규 작업. 코드 구현 없음. lerobot 레퍼런스 검색 대상 없음 (SKILL_GAP 해당 없음)
- Category A (`docs/reference/`·`.claude/`) 미변경 ✓

---

## 변경 내용 요약

`orin/config/ports.json`·`cameras.json` 의 git 추적 정책을 명문화하는 신규 정책 문서 `docs/storage/15_orin_config_policy.md` 를 작성했다. 사용자 위임 결정 (a) "git 추적 유지 + `.gitignore` 변경 X" 에 따라 결정 사유, 알려진 충돌 가능성, 환경별 override 방법, 시연장 환경 변경 시 갱신 절차를 포함했다. 04 BACKLOG #3 항목은 완료 마킹했다.

---

## code-tester 입장에서 검증 권장 사항

- **정책 문서 존재 확인**: `ls /home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/15_orin_config_policy.md` — 파일 존재 ✓
- **BACKLOG 마킹 확인**: `grep -n "#3.*완료\|완료.*#3\|15_orin_config_policy" /home/babogaeguri/Desktop/Hylion/smolVLA/docs/work_flow/specs/BACKLOG.md` — 완료 문구 확인
- **DOD 충족 확인**:
  - DOD 1: `orin/config/ports.json`·`cameras.json` 의 git 추적 vs gitignore 정책 결정 → 정책 문서 §1 ✓
  - DOD 2: 정책 문서 작성 (`docs/storage/15_orin_config_policy.md` 신규) ✓
  - DOD 3: `.gitignore` 변경 X (Category B 회피) ✓
- **git 추적 상태 미변경 확인**: `git ls-files orin/config/` 결과 3파일 그대로 (추가·제거 없음)
- **정책 문서 섹션 완결성**: §1~§8 모두 포함, 충돌 시나리오·override 방법·갱신 절차 명시

---

## 레퍼런스 활용 메모

본 TODO 는 코드 구현이 아닌 정책 문서 작성. lerobot upstream 레퍼런스 검색 불요. 기존 storage 문서 형식 (`04_devnetwork.md` 등) 을 형식 참조로 활용.
