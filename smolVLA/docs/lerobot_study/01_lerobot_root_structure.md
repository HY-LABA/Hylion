# lerobot 루트 디렉토리 구조

```
lerobot/
├── src/                      ← 실제 패키지 코드 (핵심)
├── tests/                    ← 테스트 코드
├── examples/                 ← 사용 예제 모음
├── docs/                     ← 공식 문서 (mdx 형식)
├── scripts/                  ← CI용 유틸 스크립트 (우리가 건드릴 것 아님)
│   └── ci/                   ← 메트릭 파싱 등 CI 자동화 스크립트
├── docker/                   ← Docker 환경 설정
├── benchmarks/               ← 성능 벤치마크
├── media/                    ← README에 쓰이는 이미지/영상
│
├── pyproject.toml            ← 패키지 설정 + CLI 명령어 등록 (lerobot-train 같은 것들)
├── setup.py                  ← 구버전 호환용 설치 스크립트 (pyproject.toml이 주)
├── uv.lock                   ← uv 패키지 매니저 lock 파일 (requirements.txt의 현대판)
├── requirements-ubuntu.txt   ← Ubuntu용 의존성 버전 고정 (pip용)
├── requirements-macos.txt    ← macOS용 의존성 버전 고정 (pip용)
├── requirements.in           ← 의존성 원본 (위 두 파일의 소스)
├── docs-requirements.txt     ← 문서 빌드용 의존성
├── Makefile                  ← 개발용 단축 명령 (make test, make lint 등)
│
├── README.md                 ← 프로젝트 소개
├── AGENTS.md                 ← AI 에이전트(Claude, Cursor 등)에게 주는 코드베이스 설명 ★ 신규
├── CLAUDE.md                 ← Claude Code 전용 설정 (AGENTS.md 참조) ★ 신규
├── CONTRIBUTING.md           ← 기여 방법 안내
├── AI_POLICY.md              ← HuggingFace AI 정책
├── CODE_OF_CONDUCT.md        ← 행동 강령
├── SECURITY.md               ← 보안 취약점 신고 방법
├── LICENSE                   ← Apache 2.0 라이선스
├── MANIFEST.in               ← PyPI 배포 시 포함할 파일 목록
│
├── .github/                  ← GitHub Actions CI/CD 워크플로우
├── .gitignore
├── .gitattributes
├── .dockerignore
└── .pre-commit-config.yaml   ← 커밋 전 자동 lint/format 검사 설정
```

---

## 우리 프로젝트 커스터마이징 관점

**진짜 건드릴 코어**
- `src/` — 유일하게 커스터마이징할 곳. 우리 팔 config, 모터 드라이버, smolVLA 설정 등 전부 여기
- `pyproject.toml` — 의존성 추가할 때만

**읽어두면 좋은 것**
- `AGENTS.md` — 레포 전체 아키텍처 요약이 잘 돼 있음. 코드 파악 시작점으로 유용
- `examples/tutorial/smolvla/` — smolVLA 실제 사용법 레퍼런스
- `docs/source/so101.mdx` — 모터 설정부터 캘리브레이션까지 워크플로우 순서

**건드릴 필요 없는 것**
- `tests/`, `scripts/ci/`, `benchmarks/` — lerobot 오픈소스 운영용
- `uv.lock`, `requirements-ubuntu.txt` 등 — 의존성은 `pip install -e .`로 자동 처리
- 나머지 전부 (`.github`, `Makefile`, `LICENSE`, `docker/` 등)
