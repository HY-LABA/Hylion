# context/history/ — 완료 spec 의 context 보관

`/wrap-spec` 시 완료된 spec 의 `context/*` (plan·log·verification_queue·todos) 가 `history/<NN_spec명>/` 으로 이동된다.

> **2026-05-14 fresh start**: 구 `arm_2week_plan` era 의 context history (01_teleoptest ~ 08_final_e2e, 265 파일) 는 → [`docs/storage/legacy/arm_2week_plan/work_flow/context/history/`](../../../storage/legacy/arm_2week_plan/work_flow/context/history/) 로 이관. 본 디렉터리는 `realplaying.md` 로드맵 기준 새 사이클부터 누적한다. 워커가 풀리지 않는 문제를 만났을 때 옛 era 의 사이클 흔적을 참조할 필요가 있으면 위 legacy 경로 확인.
