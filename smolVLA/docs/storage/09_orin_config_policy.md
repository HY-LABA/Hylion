# 09_orin_config_policy — `orin/config/*.json` git 추적 정책

> 작성: 2026-05-19 | spec `03_leftarm_v2_eval_003_branch` TODO-05 (M3 결정 포인트)
> 사용자 결정 (2026-05-19): **선택지 1 — 현 상태 + 정책 문서만 추가** (코드 변경 0, Category B 미발동)

---

## 결정 사항

`orin/config/ports.json` 과 `orin/config/cameras.json` 의 git 추적 정책 = **null template + deploy exclude 유지**.

| 위치 | 내용 |
|---|---|
| **repo `orin/config/*.json`** | `null` placeholder template (schema 가시화 용) — 신규 셋업 시 어떤 필드가 필요한지 노출 |
| **Orin `orin/config/*.json`** | 실측값 정본 — `check_port_and_camera_index.py` 로 측정 후 *Orin 콘솔에서 직접 기입* |
| **`scripts/deploy_orin.sh`** | `--exclude 'checkpoints/' 'config/ports.json' 'config/cameras.json'` (BACKLOG #1 fix, 2026-05-18 적용 완료) — deploy 시 Orin 의 실측값을 repo 의 null template 으로 덮어쓰지 않도록 보호 |

## 정책 근거

1. **schema 가시화**: repo 에 null template 보존하면 새 사용자/셋업 시 *어떤 필드가 필요한지* 명확. `.gitignore` 로 완전 제거하면 schema 가 commit 에서 사라져 신규 셋업 trail 부재.
2. **실측값 안전**: deploy exclude 패치 (BACKLOG #1) 가 적용되어 *실수 덮어쓰기 위험 0*. 003 사이클 (2026-05-19) Orin smoke + 20 trial 정상 작동으로 *현 정책 작동 증명*.
3. **운영 비용 최소**: 코드 변경 0 (Category B 미발동). `.gitignore` 변경 회피 — `.gitignore` 패턴은 CLAUDE.md Hard Constraints Category B (자동 재시도 X) 영역.

## 신규 셋업 절차

새 Orin / 새 시연장 셋업 시:

```bash
# Orin 콘솔에서
cd ~/smolvla
source orin/.hylion_arm/bin/activate

# (1) 실측 — 포트·카메라 인덱스 확인
python dgx/finetune/leftarm_v2/check_port_and_camera_index.py
# 또는 개별:
lerobot-find-port
lerobot-find-cameras opencv

# (2) Orin 측 orin/config/ports.json · cameras.json 에 실측값 직접 기입
#     (repo deploy 가 덮어쓰지 않음 — deploy_orin.sh exclude 패치)
nano orin/config/ports.json
nano orin/config/cameras.json
```

## 정책 위반 시 발생하는 사고 (BACKLOG #1 이력)

- 2026-05-14 식별: `deploy_orin.sh --delete` 가 `orin/checkpoints/` + `orin/config/*.json` exclude 안 함 → Orin 실측값을 repo null template 으로 덮어쓸 위험
- 2026-05-18 실제 발생 (camera_empty 추론 검증 중): 실측값 손실 → 사용자 동의 후 `--exclude` 추가 + Orin 측 ports.json·cameras.json 복원
- 본 정책으로 *동일 사고 재발 차단*

## 향후 정책 변경 게이트

만약 향후 `.gitignore` + `*.sample.json` 분리 (선택지 2) 로 전환을 검토하려면:

1. `.gitignore` 패턴 추가 = Category B → 사용자 동의 필수
2. `deploy_orin.sh` 의 `--exclude` 라인 제거 = Category B → 사용자 동의 필수
3. `*.sample.json` 신설 + repo 의 `*.json` 삭제

본 spec (03) 종료 후 별도 사이클에서 검토. 현재는 *불필요* (003 사이클 성공 + 003 결과로 정책 작동 증명).

---

## 관련 문서

- BACKLOG.md #1 (`scripts/deploy_orin.sh` exclude 패치) — 완료 (2026-05-18)
- CLAUDE.md Coupled File Rules §3 — `orin/lerobot/` 수정 시 함께 갱신 영역 (본 정책과 별개)
- CLAUDE.md Hard Constraints Category B — `.gitignore` 패턴 변경 자동 재시도 X 정책
- `~/smolvla/dgx/finetune/leftarm_v2/check_port_and_camera_index.py` — 실측 도구
