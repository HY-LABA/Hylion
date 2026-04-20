import socket


def is_online(timeout_sec: float = 1.5) -> bool:
    """Quick connectivity check using DNS endpoint reachability."""
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout_sec).close()
        return True
    except OSError:
        return False
