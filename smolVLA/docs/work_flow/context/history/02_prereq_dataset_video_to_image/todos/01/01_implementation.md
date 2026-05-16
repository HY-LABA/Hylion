# TODO-01 산출물 — researcher 보고서

> 본 todo 는 코드 작성 0. researcher 에이전트 호출 결과만 기록.
> 호출 시각: 2026-05-15
> 보고서: `docs/work_flow/context/research/m1.5_video_decode_oom.md`

## verdict

**`NEEDS_INVESTIGATION`** — image 변환 결정은 타당하나, 실험 A (환경 cleanup 강화 후 시도 3) 를 먼저 40분 시도하는 것이 강력 권장됨. 실패 시 image 변환 confirm.

## 핵심 발견 (메인 → 사용자 보고용)

1. **lerobot `video_utils.py` 코드 리뷰 — stream.close() 누락 직접 확인**
   - `decode_video_frames_torchvision` 이 `container.close()` 만, `stream.close()` 없음
   - 매 배치마다 새 VideoReader → 수만 번 반복 → reference cycle 누적 (PyAV Issue #1117 패턴 일치)
2. **lerobot streaming_dataset 는 torchcodec 전용 — DGX 환경 사용 불가 확정** (옵션 5 폐기)
3. **torchcodec aarch64 공식 wheel 없음 확정** (옵션 7 장기 backlog)
4. **시도 1·2 의 dmesg `task=code` 2회 OOM-kill** → VSCode 동시 점유가 baseline 메모리 잠식 → cleanup 강화의 의의

## §5 추천 — 2단계 순차 접근

**1단계 (45분)**: 실험 A — cleanup 강화 + 시도 3
- `pkill -9 -f code`, `pkill -9 -f claude`, Firefox 종료 → `free -h` MemAvailable 100GB+ 확인 → 학습 30분 관찰
- 성공: image 변환 불요. 실패: image 변환 confirm.

**2단계 (실험 A 실패 시)**: 옵션 3 (image dataset 변환) — researcher §5 단일 추천

## 메인 다음 액션 (사용자 결정 게이트)

verdict `NEEDS_INVESTIGATION` → spec 본문 §"researcher verdict 분기" 룰에 따라 사용자 결정 필요. TODO-02·03 자동 dispatch X. 메인이 AskUserQuestion 으로 다음 선택지 제시:

A. 실험 A 먼저 시도 (40분, 코드 0)
B. image 변환 직행 (TODO-02·03 그대로)
C. 사용자 추가 의견

## ANOMALIES 신호

researcher 가 산출 경로 `docs/work_flow/context/research/m1.5_video_decode_oom.md` 로 Write 하지 않고 텍스트로만 반환 — 메인이 사후 직접 Write 로 복구. 분류: `ORCHESTRATOR_GAP` (메인의 dispatch 프롬프트가 산출 의무를 명시했으나 agent 가 미이행). reflection 분석 대상.
