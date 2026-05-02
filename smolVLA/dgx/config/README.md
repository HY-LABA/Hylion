# dgx/config/ — DGX 학습 설정 캐시

> 책임: DataCollector 로부터 수신하는 HF 데이터셋 repo_id 목록 등 학습 관련 설정 캐시 관리. 학습 스크립트가 매번 수동 입력하지 않도록 영속화.
> 신설: 04_infra_setup TODO-X2 (2026-05-01)
> 형제: `orin/config/` (Orin 측 cached config — SO-ARM 포트 / 카메라 인덱스)

---

## 자산

| 파일 | 스키마 | 갱신 주체 |
|---|---|---|
| `dataset_repos.json` | HF Hub repo_id + rsync source/dest 양쪽 스키마 (placeholder) | TODO-T1 결정 후 사용자 수기 갱신 또는 스크립트 |

---

## `dataset_repos.json` 스키마

DataCollector ↔ DGX 데이터 전송 방식은 **HF Hub + rsync 둘 다** (TODO-T1 사용자 결정). 두 방식을 모두 지원하는 스키마:

```json
{
  "datasets": [
    {
      "name": "<dataset_name>",
      "hf_hub": {
        "repo_id": "<HF_USER>/<dataset_name>",
        "private": false
      },
      "rsync": {
        "source": "<datacollector_host>:<dataset_local_path>",
        "dest": "/home/laba/smolvla/.hf_cache/lerobot/<HF_USER>/<dataset_name>"
      },
      "active_method": "hf_hub"
    }
  ]
}
```

필드 설명:

| 필드 | 타입 | 설명 |
|---|---|---|
| `name` | string | 로컬 식별자 (본 프로젝트 컨벤션) |
| `hf_hub.repo_id` | string | lerobot 표준 `{hf_username}/{dataset_name}` 형식 (`lerobot-record --dataset.repo_id`, `lerobot-train --dataset.repo_id` 와 동일) |
| `hf_hub.private` | bool | HF Hub private repo 여부 |
| `rsync.source` | string | rsync 원본 경로 (`<host>:<path>` 또는 절대 경로) |
| `rsync.dest` | string | DGX 측 수신 경로 (HF_HOME 기준 표준 위치 사용 권장) |
| `active_method` | `"hf_hub"` \| `"rsync"` | 현재 사용할 전송 방식 |

`hf_hub.repo_id` 는 lerobot upstream `DatasetRecordConfig.repo_id` (lerobot_record.py) 와 동일 포맷을 따른다.

---

## placeholder 값 (현재)

`dataset_repos.json` 은 placeholder 상태. 실 데이터셋 정보는 05_leftarmVLA 진입 시 (TODO-T1 결정 후) 사용자가 채운다.

---

## 갱신 방법

```bash
# 수기 갱신 (현재 방식)
vim ~/smolvla/dgx/config/dataset_repos.json

# 스크립트 갱신 (TODO-T1 결정 후 구현 예정)
# bash scripts/register_dataset.sh --name <name> --repo-id <HF_USER/name>
```

---

## git 추적 정책

- **본 README + dataset_repos.json 모두 git 추적** (schema 구조는 안정적, 실 값은 TODO-T1 이후 채워짐)
- 실 repo_id 는 사용자 HF 계정 의존 — 다른 인스턴스에서 충돌 가능. 운용 시 주의.

---

## lerobot 표준 데이터셋 경로 (본 디렉터리 X)

lerobot-train 이 HF Hub 에서 자동 다운로드한 데이터셋의 표준 캐시 위치:

```
$HF_HOME/lerobot/<HF_USER>/<dataset_name>/
# 본 프로젝트: /home/laba/smolvla/.hf_cache/lerobot/...
```

본 `dgx/config/` 는 데이터셋 자체가 아니라 **어떤 데이터셋을 쓸지 메타 정보** 만 관리. 캐시 위치는 lerobot 표준 그대로 사용.

---

## 참고

- `docs/storage/09_dgx_structure.md` §4-3 (DataCollector ↔ DGX 인터페이스)
- `docs/work_flow/specs/04_infra_setup.md` TODO-T1 (전송 방식 결정 + 스크립트)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — DatasetRecordConfig.repo_id 패턴
- `orin/config/README.md` — Orin 측 cached config 패턴 (형제 문서)
