# Phase 3 검증 대기 큐

> Phase 2 진행 중 prod-test-runner 가 완료한 항목 + 사용자 실물 검증이 필요한 항목을 누적. 모든 todo 자동화 종료 시 메인이 본 큐를 사용자에게 일괄 제시.

## 형식

각 항목:

```markdown
### [TODO-XX] (제목)

- **상태**: 자동 검증 통과 / 실패 / N.A.
- **사용자 검증 필요 사항**:
  1. (구체 절차)
  2. ...
- **prod-test-runner 결과 요약**: ...
- **참고 파일**: `context/todos/XX/03_prod-test.md`
```

---

## 활성 spec: 02_leftarm_v2_finetune

### [TODO-03-C] Orin SSH 점검 + ckpt 다운로드 + leftarm_v2 추론 entry 검증

- **상태**: NEEDS_USER_VERIFICATION (cycle 3 — 자동 검증 통과, PHYS_REQUIRED 항목 Phase 3 위임)
- **cycle 3 자동 통과 항목**:
  - peft 0.19.1 설치 + import 확인 ✅
  - leftarm_v2_inference.py top-level import smoke ✅
  - LoRA 로드 smoke: SmolVLAPolicy (smolvla_base) + PeftModel (leftarm_v2 adapter) CUDA 결합 ✅
  - download/check subcommand 회귀 없음 (n_action_steps=50 재확인) ✅
  - wrapper dry-run: 환경 의존 에러 (follower_port null) — 코드 결함 아님 ✅
  - 카메라 자동 발견 동작 (top:0, wrist:2 — 2대) ✅
- **사용자 검증 필요 사항** (PHYS_REQUIRED — 시연장):
  1. **orin/config 설정** — `ports.json` follower_port, `cameras.json` top.index/wrist.index 시연장에서 채우기. 또는 환경 변수 override (`FOLLOWER_PORT=<port> TOP_IDX=<idx> WRIST_IDX=<idx>`).
  2. **live task1 10 trial** — `bash ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh live task1`. 성공/실패/추론 품질 성능평가 시트(TODO-03-A)에 기록.
  3. **live task2 10 trial** — `bash ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh live task2`. 성공/실패/추론 품질 기록.
  4. **camera3 누락 영향 관찰** — 2카메라(top/wrist)만으로 추론 품질 정상 여부 확인. 이상 동작 시 `empty_cameras=1` 검토.
- **prod-test 결과 요약** (cycle 3): peft 0.19.1, LoRA 로드 OK (PeftModel, CUDA), import smoke OK, download/check 정상, awaits_user (follower_port/cameras null) 잔존
- **참고 파일**: `context/todos/03C/03_prod-test.md` § Cycle 3

- **cycle 4 (rotation 정합 fix 완료, 2026-05-18)**: leftarm_v2_inference.py + cameras.json schema 확장(rotation/width/height/fps/fourcc/flip) 재배포. import smoke OK, top rotation=-90→Cv2Rotation.ROTATE_270 enum 변환 OK, wrist rotation=0 OK. cameras.json index null 유지 — 사용자 시연장 채우기 대기.
- **참고 파일 (cycle 4)**: `context/todos/03H/03_prod-test.md`

### Phase 3 사용자 검증 결과 (2026-05-18 /verify-result)

| 항목 | 결과 |
|---|---|
| 1. orin/config null 채우기 | ✅ 완료 — cameras.json (top:0, wrist:2), ports.json (/dev/ttyACM0) 사용자 채움. DGX 의 leftarm_test_follower.json cal 파일도 Orin lerobot 캐시로 transfer (ad-hoc) |
| 2. live task1 10 trial | ⚠️ **단축 1 trial 실시** (front, max-steps 500). 결과: ❌ 잡기 실패 (헛스윙). 9 trial 미실시 — 단축 결정 |
| 3. live task2 10 trial | ⚠️ **단축 1 trial 실시** (front, max-steps 1000). 결과: ❌ 동작 불완전 (캔 방향 이동만). 9 trial 미실시 — 단축 결정 |
| 4. camera3 누락 영향 관찰 | ✅ 정성 기록 — 동작 자체 부드럽고 모터 이상 없음, 정책 *판단력* 한계가 핵심 (camera3 영향 미미 추정). 평가 시트 정성 메모 참조 |

**단축 결정 사유** (사용자, 2026-05-18): 첫 trial 결과 동작 형편없음 → 정량 평가 자체가 무의미 결론. 학습 방법 + 데이터셋 재정렬이 정확한 다음 단계. spec TODO-03 (d) 의 *0-20% 영역 분기* 진입 결정 (전체 0/2 = 0%).

**DOD 정합**: 본 TODO-03 의 (d) "M2 본 학습 진입 가치 정량 판단" 의도 충족 — 단순 직진 X, 재정렬 필요 정확히 식별. 다음 사이클 Phase 1 결정 영역: (1) 학습 방법 (LoRA·VLM·epoch·lr), (2) 데이터셋 확장 (M1 잔여 + 다양성), (3) 학습 노드, (4) 검증 시점.

**상태**: PHASE3_COMPLETE — `/wrap-spec` 진행 가능.
