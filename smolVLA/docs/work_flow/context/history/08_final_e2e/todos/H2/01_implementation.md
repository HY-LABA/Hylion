# TODO-H2 — Implementation

> 작성: 2026-05-04 10:00 | task-executor | cycle: 1

## 목표

overview (OV5648, 68°) vs wrist (U20CAM-720P, FOV-H 102°) 카메라 사양 차이에 따른 코드·config 영향 검토 + 적용. H1 Recommended(§7 수량 갱신) 흡수.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/02_hardware.md` | M | §7 수량 "2대→1대 (overview, SO-ARM 관측용)" + §9 카메라 키 컨벤션·분기 결과·잠재 리스크 신규 |
| `docs/work_flow/specs/BACKLOG.md` | M | 08_final_e2e 섹션 신규 + wrist 관련 BACKLOG 2건 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: orin/lerobot/ 미변경, orin/pyproject.toml 미변경 → Coupled 파일 갱신 불필요 ✓
- 레퍼런스 활용: 코드 분기 불필요로 판정 — 신규 코드 작성 없음. 레퍼런스 검색 수행 (하단 §검토 상세 참조)

## 검토 영역별 결과

### 1. `dgx/interactive_cli/flows/record.py` `--robot.cameras` 인자

**현재 상태** (build_record_args() line 284~288):
```python
cameras_str = (
    f"{{wrist_left: {{type: opencv, index_or_path: {cam_wrist_left_index},"
    f" width: 640, height: 480, fps: 30, fourcc: MJPG}},"
    f" overview: {{type: opencv, index_or_path: {cam_overview_index},"
    f" width: 640, height: 480, fps: 30, fourcc: MJPG}}}}"
)
```

**검토 결과**: 두 카메라 동일 사양(640×480, 30fps, MJPG) 적용 중.
- U20CAM-720P: 지원 해상도 1280×720 / 800×600 / 640×480 — 640×480 지원 ✓
- U20CAM-720P: 출력 포맷 MJPEG / YUY2 — MJPG ✓
- OV5648: 출력 포맷 MJPEG / YUV2 — MJPG ✓

**판정**: 코드 분기 불필요. 640×480 + MJPG는 두 카메라 모두 지원. U20CAM-720P 최대 해상도 1280×720 활용은 옵션이나 USB 2.0 대역폭 경합 (§5-2 패턴) + 모델 입력 해상도 기준(보통 224×224 resize)을 고려하면 현재 640×480이 적절.

### 2. `orin/config/cameras.json` slot 별 분기

**현재 상태**:
```json
{
  "top": {"index": null, "flip": false},
  "wrist": {"index": null, "flip": false}
}
```

**검토 결과**: cameras.json은 index + flip만 저장. fourcc 필드 없음. hil_inference.py는 `OpenCVCameraConfig(index_or_path=idx, width=640, height=480, fps=30)`으로 fourcc 지정 없음 — OpenCV 기본(YUYV)으로 열림.

참고: hil_inference.py에서 fourcc 미지정은 추론 단에서 허용됨 (단일 카메라 단독 capture이고 SO-ARM 직렬 통신과 대역폭 경합이 낮음). 반면 DGX record.py는 SO-ARM 2개 + 카메라 2개 동시 USB 2.0 경합 상황이라 MJPG 강제.

**판정**: cameras.json 구조 변경 불필요. wrist flip은 기본값 false 유지 — 물리 장착 방향은 C1 시연장 셋업 후 결정 (BACKLOG #2).

### 3. `orin/inference/hil_inference.py` flip 인자 기본값

**현재 상태** (line 288):
```python
parser.add_argument("--flip-cameras", type=parse_camera_names, default=set(), ...)
```
flip 기본값 = 빈 set (플립 없음).

**검토 결과**: wrist 광각 카메라의 물리 장착 방향은 실물 셋업 시 확인 필요. 코드 기본값 `set()` 그대로 유지 — 운영 단에서 cameras.json.wrist.flip=true 또는 --flip-cameras wrist로 제어. 03 BACKLOG #16에서 이미 추적 중.

**판정**: 코드 변경 불필요.

### 4. §5-2 fourcc=MJPG 패턴 적용 확인

두 카메라 모두 MJPEG 지원. DGX record.py 이미 fourcc=MJPG 강제 적용 중 (§5-2 패턴 반영됨). 추가 변경 불필요.

### 5. 카메라 키 컨벤션 불일치 (발견 사항)

| 노드 | 키 | 파일 |
|---|---|---|
| DGX 수집 | `wrist_left`, `overview` | dgx/interactive_cli/flows/record.py cameras_str |
| Orin 추론 | `top`, `wrist` | orin/config/cameras.json, hil_inference.py |
| 데이터셋 (svla_so100_pickplace) | `top`, `wrist` | 외부 자원 |

불일치 원인: DGX record.py는 legacy datacollector record.py에서 이식 시 `wrist_left`/`overview` 키 그대로 사용. Orin 추론은 svla_so100_pickplace 컨벤션인 `top`/`wrist` 사용.

실제 영향: lerobot-record로 수집 시 데이터셋에 `wrist_left`/`overview` 키로 저장됨. 이 데이터셋으로 fine-tune 시 모델 내부 camera 키 매핑이 svla_so100_pickplace의 `top`/`wrist` 기대와 다를 수 있음. 단 smolvla는 camera1/2/3 슬롯 기반이고 키는 내부적으로 정렬 순서로 처리되므로 정확한 영향은 학습·추론 결과로 확인 필요.

**판정**: 현재 사이클(08_final_e2e) 범위에서 코드 변경 X (큰 리팩토링 제외 제약). C2 수집 결과 데이터셋 키 확인 후 필요 시 09 사이클에서 dgx/record.py 키 `overview`→`top`, `wrist_left`→`wrist` 통일 검토.

## 변경 내용 요약

코드 변경 없음 — 검토 결과 overview(OV5648)와 wrist(U20CAM-720P) 사양 차이가 현 코드에 분기 필요한 수준의 불호환을 유발하지 않음. 두 카메라 모두 640×480@30fps MJPG 지원, cameras.json 구조 변경 불필요, hil_inference.py flip 기본값 `set()` 유지.

문서 변경 2건: (1) `docs/storage/02_hardware.md` §7 수량 갱신 (H1 Recommended 흡수) + §9 카메라 키 컨벤션·분기 결과·잠재 리스크 신규 섹션. (2) `BACKLOG.md` 08_final_e2e 섹션 신규 + wrist 광각 분포 차이 리스크·flip 미결 2건 추가.

## code-tester 입장에서 검증 권장 사항

- grep: `docs/storage/02_hardware.md` §7 수량 "1대 (overview" 포함 확인
- grep: `docs/storage/02_hardware.md` §9 키워드 "9) 카메라 키 컨벤션" 존재
- grep: `BACKLOG.md` `08_final_e2e` 섹션 + "wrist 광각" 항목 #1 존재
- grep: `BACKLOG.md` "wrist 카메라 장착 방향 flip 미결" 항목 #2 존재
- 코드 파일 미변경 확인: `dgx/interactive_cli/flows/record.py`, `orin/config/cameras.json`, `orin/inference/hil_inference.py` 변경 없음 (DOD "코드 분기 필요 시 적용 — 불필요 판정")
- H1 Recommended 흡수 확인: §7 `2대 (SO-ARM 관측용)` 없음

## 잠재 리스크

1. **wrist 광각 분포 차이** (BACKLOG #1): U20CAM-720P 102° vs smolvla_base 사전학습 분포 미확인. C2/T1/I1 정성 차이 가능. 03 BACKLOG #11 연계.
2. **DGX record.py 카메라 키 불일치** (발견): `wrist_left`/`overview` vs `top`/`wrist`. 수집 데이터셋 키 불일치 → fine-tune 시 카메라 슬롯 정렬 순서 의존. 09 사이클 처리 검토.
3. **hil_inference.py fourcc 미지정**: Orin 추론 단에서 OpenCV 기본 fourcc(YUYV) 사용. 단일 카메라 capture라 대역폭 문제 없으나, 향후 카메라 추가 시 §5-2 MJPG 패턴 적용 검토 필요.
