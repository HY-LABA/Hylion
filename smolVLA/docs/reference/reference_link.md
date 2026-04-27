# Reference Links

`smolVLA/docs/reference/` 하위 외부 참조 자료의 원본 출처(upstream)와 로컬 경로를 정리한 인덱스.

---

## 1. 서브모듈 (읽기 전용 upstream)

| 로컬 경로 | Upstream URL | 비고 |
|---|---|---|
| [lerobot/](lerobot/) | https://github.com/huggingface/lerobot | HuggingFace lerobot upstream. 수정 금지 — `orin/lerobot/`에서 wrapping/extending |
| [reComputer-Jetson-for-Beginners/](reComputer-Jetson-for-Beginners/) | https://github.com/Seeed-Projects/reComputer-Jetson-for-Beginners | Seeed Jetson beginner 튜토리얼 모음 |
| [seeed-lerobot/](seeed-lerobot/) | https://github.com/Seeed-Projects/lerobot | Seeed-Projects 포크 (안정 버전). Seeed 튜토리얼이 권장하는 클론 대상 |

업데이트 방법:
```bash
git submodule update --remote smolVLA/docs/reference/lerobot
git submodule update --remote smolVLA/docs/reference/reComputer-Jetson-for-Beginners
git submodule update --remote smolVLA/docs/reference/seeed-lerobot
```

---

## 2. NVIDIA PyTorch on Jetson 공식 문서

로컬 경로: [nvidia_official/](nvidia_official/)

| 로컬 파일 | 원본 문서 / 다운로드 링크 |
|---|---|
| [nvidia_official/Install-PyTorch-Jetson-Platform.md](nvidia_official/Install-PyTorch-Jetson-Platform.md) | NVIDIA — Installing PyTorch For Jetson Platform (Installation Guide) `SWE-SWDOCTFX-001-INST_v001`, April 2026 |
| [nvidia_official/Install-PyTorch-Jetson-Platform.pdf](nvidia_official/Install-PyTorch-Jetson-Platform.pdf) | 위 문서의 원본 PDF |
| [nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md](nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.md) | NVIDIA — PyTorch for Jetson Platform Release Notes `SWE-SWDOCTFX-001-RELN_v001`, April 2026 |
| [nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.pdf](nvidia_official/Install-PyTorch-Jetson-Platform-Release-Notes.pdf) | 위 문서의 원본 PDF |

관련 온라인 참조:
- NVIDIA Developer Forums — [PyTorch for Jetson (공식 스레드)](https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048)
- NVIDIA Developer Forums — [Installing PyTorch & Torchvision for JetPack 6.2 and CUDA 12.6](https://forums.developer.nvidia.com/t/installing-pytorch-torchvision-for-jetpack-6-2-and-cuda-12-6/346074)
- NVIDIA redistributables (JP 버전별 wheel): `https://developer.download.nvidia.com/compute/redist/jp/`

---

## 3. Seeed Studio Wiki 번역 문서

로컬 경로: [seeedwiki/](seeedwiki/)

| 로컬 파일 | 원본 출처 |
|---|---|
| [seeedwiki/seeedwiki_so101.md](seeedwiki/seeedwiki_so101.md) | [SeeedStudio Wiki — Getting started with SO-ARM100 and SO-ARM101 robotic arm with LeRobot](https://wiki.seeedstudio.com/lerobot_so100m_new/) — 한국어 전체 번역본 |

관련 Seeed 프로젝트:
- [Seeed-Projects/lerobot (포크, 안정 버전)](https://github.com/Seeed-Projects/lerobot) — Seeed 튜토리얼이 권장하는 클론 대상 (upstream과 별개)
- [Seeed-Projects/Seeed_RoboController](https://github.com/Seeed-Projects/Seeed_RoboController) — SoARM 중간 위치 캘리브레이션 도구
- reComputer Jetson Mini J4012 Orin NX 16GB 제품 페이지: https://www.seeedstudio.com/reComputer-J3010-p-5589.html

---

## 4. 기타 외부 참조

현재 스코프(Orin 추론 / SO-ARM101 / SmolVLA)에 직접 관련 있는 링크만 유지.
향후 단계에서 필요해질 수 있는 항목은 **비고**로 맥락을 명시.

| 링크 | 비고 |
|---|---|
| [SeeedStudio Wiki — LeRobot SO-100M 튜토리얼 (원문)](https://wiki.seeedstudio.com/lerobot_so100m_new/) | seeedwiki_so101.md 번역 원본 |
| [HuggingFace LeRobot Docs](https://huggingface.co/docs/lerobot) | lerobot 공식 문서 |
| [HuggingFace dataset visualizer](https://huggingface.co/spaces/lerobot/visualize_dataset) | Orin에서 데이터 수집 시 참고 (`lerobot-dataset-viz` 보조) |
| [SmolVLA 파인튜닝 Colab](https://colab.research.google.com/github/huggingface/notebooks/blob/main/lerobot/training-smolvla.ipynb) | 향후 DGX 학습 스택 설계 시 참고 예제 |
| [Accelerate 공식 문서](https://huggingface.co/docs/accelerate/index) | 향후 DGX 다중 GPU 학습 시 참고 |
