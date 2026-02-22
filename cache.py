# cache.py
import os
from typing import Set


class ProcessedCache:
    """Кэш ID обработанных писем с persistence в файл."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._cache: Set[str] = self._load()

    def _load(self) -> Set[str]:
        if not os.path.exists(self.filepath):
            return set()
        with open(self.filepath, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}

    def contains(self, msg_id: str) -> bool:
        return msg_id in self._cache

    def add(self, msg_id: str) -> None:
        if msg_id in self._cache:
            return
        self._cache.add(msg_id)
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(f"{msg_id}\n")
