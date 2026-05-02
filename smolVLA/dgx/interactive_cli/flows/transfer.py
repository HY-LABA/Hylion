"""interactive_cli flow 7 — 전송 방식 선택 (H-(b) 재정의).

사용자 결정 H-(b) (06_dgx_absorbs_datacollector, 2026-05-02):
  2분기 메뉴 (rsync DGX·Orin 옵션 완전 폐지):
    (1) 로컬 저장만    — DGX 로컬에 이미 저장됨 안내
    (2) HF Hub 백업도 같이 — push_dataset_hub.sh 호출 + 로컬 보관도 유지

  (b) 선택 시: datacollector 의 push_dataset_hub.sh 호출 패턴 그대로 + 로컬 보관 유지.
  rsync DGX / Orin rsync 옵션은 완전 폐지 (메뉴 자체에서 삭제).

레퍼런스 (이식 원본):
  docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/transfer.py
  _check_hf_token(): 그대로 재사용 (push_dataset_hub.sh line 104~117 패턴 미러)
  _transfer_to_hub(): 그대로 재사용 (스크립트 경로 자동 해석 동일)

이식 변경 사항:
  - 메뉴 재정의: (1) HF Hub / (2) rsync DGX / (3) 안함
               → (1) 로컬 저장만 / (2) HF Hub 백업도 같이
  - rsync 관련 함수 (_guide_rsync_to_dgx) 제거
  - _keep_local 안내 메시지 dgx 경로 맞춤
  - flow7_select_transfer: H-(b) 메뉴 적용 (2 옵션)
  - 전송 완료 후 결과만 반환 (G-4 학습 전환 prompt 는 mode.py 책임)

push_dataset_hub.sh 레퍼런스:
[1] push_dataset_hub.sh pre-check (line 104~117):
    HF_TOKEN 환경변수 또는 huggingface-cli 로그인 확인
    HF_AUTH_OK: "token" / "cached" / "false"

[2] push_dataset_hub.sh 인자 형식 (line 6~14):
    bash push_dataset_hub.sh \\
        --dataset ~/smolvla/dgx/data/<name> \\
        --repo-id <HF_USER>/<REPO_NAME>
    [--private]
"""

import os
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# HF Token 확인 (push_dataset_hub.sh line 104~117 패턴 미러)
# ---------------------------------------------------------------------------

def _check_hf_token() -> tuple[bool, str]:
    """HF 인증 정보 유무 확인.

    push_dataset_hub.sh line 104~117 패턴 미러:
      HF_TOKEN 환경변수 우선 → huggingface-cli cached token 확인.

    Returns:
        (ok, auth_type): auth_type in {"token", "cached", "none"}
    """
    hf_token = os.environ.get("HF_TOKEN", "")
    if hf_token:
        return True, "token"

    try:
        result = subprocess.run(
            ["python3", "-c",
             "from huggingface_hub import HfFolder; t=HfFolder.get_token(); exit(0 if t else 1)"],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            return True, "cached"
    except FileNotFoundError:
        pass

    return False, "none"


# ---------------------------------------------------------------------------
# HF Hub 업로드 (원본 _transfer_to_hub 그대로)
# ---------------------------------------------------------------------------

def _transfer_to_hub(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
    private: bool = False,
) -> int:
    """push_dataset_hub.sh 직접 호출.

    원본 transfer.py _transfer_to_hub 패턴 그대로.
    스크립트 경로: script_dir.parent / "scripts" / "push_dataset_hub.sh"
    (dgx/interactive_cli/flows/ → dgx/scripts/)

    Args:
        script_dir: flows/ 디렉터리 경로
        local_dataset_path: 로컬 dataset 경로
        repo_id: HF Hub repo ID
        private: private repo 여부

    Returns:
        subprocess returncode
    """
    push_script = script_dir.parent / "scripts" / "push_dataset_hub.sh"

    if not push_script.exists():
        print(f"[flow 7] ERROR: push_dataset_hub.sh 미발견: {push_script}", file=sys.stderr)
        print("         dgx/scripts/push_dataset_hub.sh 를 확인하세요. (X3 이식 대상)", file=sys.stderr)
        return 1

    cmd = [
        "bash", str(push_script),
        "--dataset", local_dataset_path,
        "--repo-id", repo_id,
    ]
    if private:
        cmd.append("--private")

    result = subprocess.run(cmd, check=False)
    return result.returncode


# ---------------------------------------------------------------------------
# 로컬 저장 안내 (H-(b) 옵션 1)
# ---------------------------------------------------------------------------

def _keep_local_dgx(local_dataset_path: str, repo_id: str) -> None:
    """로컬 DGX 저장 안내.

    H-(b) 옵션 1: 로컬 저장만.
    DGX 자체가 수집 노드이므로 이미 로컬에 저장된 상태.
    나중에 HF Hub 업로드하려면 push_dataset_hub.sh 를 직접 실행.
    """
    print()
    print(f"[flow 7] 로컬 저장 유지: {local_dataset_path}")
    print("  나중에 HF Hub 에 업로드하려면:")
    print(
        f"  bash dgx/scripts/push_dataset_hub.sh"
        f" --dataset {local_dataset_path} --repo-id {repo_id}"
    )


# ---------------------------------------------------------------------------
# flow 7 메인 함수 (H-(b) 재정의 — 2 옵션)
# ---------------------------------------------------------------------------

def flow7_select_transfer(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
) -> None:
    """flow 7: 전송 방식 선택 (H-(b) 결정 적용).

    H-(b) 메뉴:
      (1) 로컬 저장만    — DGX 에 이미 저장됨 안내
      (2) HF Hub 백업도 같이 — push_dataset_hub.sh 호출 + 로컬 보관 유지

    rsync DGX / Orin rsync 옵션 완전 폐지.
    전송 완료 후 결과만 반환 (G-4 학습 전환 prompt 는 mode.py 책임).

    Args:
        script_dir: flows/ 디렉터리 경로
        local_dataset_path: lerobot-record 가 저장한 로컬 경로 (dgx/data/<name>)
        repo_id: HF Hub repo ID (flow 6 에서 입력받은 값)
    """
    print()
    print("=" * 60)
    print(" flow 7 — 전송 방식 선택")
    print("=" * 60)
    print()
    print(f"데이터셋이 저장되었습니다: {local_dataset_path}")
    print()
    print("전송 방식을 선택해주세요:")
    print("  (1) 로컬 저장만 (DGX 에 이미 저장됨)")
    print("  (2) HF Hub 백업도 같이 (인터넷 필요 + 로컬 보관 유지)")
    print()

    while True:
        try:
            raw = input("번호 선택 [1~2]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("[flow 7] 종료됩니다. 로컬 저장 유지.")
            _keep_local_dgx(local_dataset_path, repo_id)
            return

        if raw == "1":
            # 로컬 저장만
            _keep_local_dgx(local_dataset_path, repo_id)
            return

        elif raw == "2":
            # HF Hub 업로드 — 토큰 확인 먼저
            token_ok, auth_type = _check_hf_token()
            if not token_ok:
                print()
                print("[flow 7] HuggingFace 인증 정보 없음.")
                print("  옵션 A (권장): export HF_TOKEN=hf_xxxxxxxxxx")
                print("  옵션 B: huggingface-cli login")
                print()
                print("인증 설정 후 다시 선택하세요. (또는 (1) 로컬 저장만 선택)")
                continue

            print(f"[flow 7] HF 인증 확인 ({auth_type})")
            try:
                private_input = input("private repo 로 업로드? [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                private_input = "n"

            private = private_input in ("y", "yes")

            returncode = _transfer_to_hub(
                script_dir, local_dataset_path, repo_id, private
            )
            if returncode == 0:
                print(f"[flow 7] HF Hub 업로드 완료: https://huggingface.co/datasets/{repo_id}")
            else:
                print(f"[flow 7] HF Hub 업로드 실패 (returncode={returncode}). 나중에 재시도 안내:")
                print(
                    f"  bash dgx/scripts/push_dataset_hub.sh"
                    f" --dataset {local_dataset_path} --repo-id {repo_id}"
                )

            # 로컬 보관도 유지 — 업로드 성공·실패 무관
            print()
            print(f"[flow 7] 로컬 보관 유지: {local_dataset_path}")
            return

        else:
            print("  1, 2 중 하나를 입력하세요.")
