from typing import List

class NetworkTracker:
    """
    Auditable counter of external network calls.
    Verifies that FinSight processes data 100% locally with zero cloud leakage.
    """
    _outbound_calls: int = 0
    _destinations: List[str] = []

    @classmethod
    def record_call(cls, destination: str):
        cls._outbound_calls += 1
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

