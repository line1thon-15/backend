from typing import Protocol


class DatabaseProbe(Protocol):
    def ping(self) -> bool: ...
