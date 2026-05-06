import socket
from typing import Iterable


DEFAULT_PROBE_TARGETS = (
    ("8.8.8.8", 53),
    ("1.1.1.1", 53),
    ("www.google.com", 443),
    ("www.naver.com", 443),
)


def _probe_target(host: str, port: int, timeout_sec: float) -> bool:
    try:
        connection = socket.create_connection((host, port), timeout=timeout_sec)
    except OSError:
        return False

    connection.close()
    return True


def is_online(timeout_sec: float = 1.5, targets: Iterable[tuple[str, int]] = DEFAULT_PROBE_TARGETS) -> bool:
    """Return True when at least one lightweight outbound connectivity probe succeeds."""
    for host, port in targets:
        if _probe_target(host, port, timeout_sec):
            return True
    return False
