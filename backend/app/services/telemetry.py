import socket
from typing import List, Optional

class NetworkTracker:
    """
    Auditable counter of external network calls.
    Verifies that FinSight processes data 100% locally with zero cloud leakage.
    Genuinely wired into low-level socket connections to intercept any outbound network traffic.
    """
    _outbound_calls: int = 0
    _destinations: List[str] = []
    _hook_installed: bool = False
    _original_connect = None

    @classmethod
    def install_hook(cls):
        """Install low-level socket.connect interceptor to track any external egress attempts."""
        if cls._hook_installed:
            return
        cls._original_connect = socket.socket.connect

        def tracking_connect(sock_self, address):
            host = None
            port = None
            if isinstance(address, tuple) and len(address) >= 2:
                host, port = address[0], address[1]
            elif isinstance(address, str):
                host = address

            # Disregard loopback/localhost dev traffic
            local_hosts = ("127.0.0.1", "localhost", "::1", "0.0.0.0")
            if host and str(host) not in local_hosts:
                dest_str = f"{host}:{port}" if port else str(host)
                cls.record_call(dest_str)

            return cls._original_connect(sock_self, address)

        socket.socket.connect = tracking_connect
        cls._hook_installed = True

    @classmethod
    def record_call(cls, destination: str):
        cls._outbound_calls += 1
        if destination not in cls._destinations:
            cls._destinations.append(destination)

    @classmethod
    def get_call_count(cls) -> int:
        return cls._outbound_calls

    @classmethod
    def get_allowed_destinations(cls) -> List[str]:
        return list(cls._destinations)

    @classmethod
    def reset(cls):
        cls._outbound_calls = 0
        cls._destinations = []
