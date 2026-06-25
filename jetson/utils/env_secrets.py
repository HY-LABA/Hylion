"""Hylion 의 .env 시크릿 로더.

`groq_llm` / `groq_whisper` / `llm_runtime` 는 `os.getenv("GROQ_API_KEY")` 만
보지만 운영 환경에서는 키를 `~/Hylion/.env` 에 두는 게 정석(`.gitignore` 138 행
에 등록되어 있어 repo 노출 위험이 없음). 셸 export 에 의존하면 비-인터랙티브
SSH 세션·systemd unit 에서 키가 빠지는 사고가 반복돼서, 이 모듈이
`os.environ` 보다 먼저 `.env` 캐시를 한 번 읽고 비어 있는 키를 보충해 준다.

`jetson/expression/speaker.py` 의 Clova 패턴(`_read_env_file` /
`_get_env_value`)을 공용으로 옮긴 것 — 새 secret 키도 여기에 통일한다.
"""

from __future__ import annotations

import os
from pathlib import Path


_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _read_env_file() -> dict[str, str]:
	env_map: dict[str, str] = {}
	if not _ENV_PATH.exists():
		return env_map
	try:
		for raw_line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
			line = raw_line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue
			key, _, value = line.partition("=")
			env_map[key.strip()] = value.strip().strip('"').strip("'")
	except Exception:
		pass
	return env_map


_DOTENV_CACHE: dict[str, str] = _read_env_file()


def get_secret(key: str, default: str = "") -> str:
	"""Return the secret value. Shell env wins; `.env` cache fills the gap."""
	value = os.getenv(key, "").strip().strip('"').strip("'")
	if value:
		return value
	return _DOTENV_CACHE.get(key, default)


def ensure_env_from_dotenv(key: str) -> str:
	"""Same precedence as :func:`get_secret`, but additionally populates
	``os.environ[key]`` so SDKs that read the env directly (e.g. ``Groq()``)
	pick up the value transparently. Returns the resolved value (empty when
	neither source has it)."""
	resolved = get_secret(key)
	if resolved and not os.getenv(key):
		os.environ[key] = resolved
	return resolved
