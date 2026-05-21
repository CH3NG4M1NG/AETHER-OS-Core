from __future__ import annotations


class AIVirtualMemorySystem:
    """Tensor/KV/embedding virtual memory policy simulator."""

    def __init__(self) -> None:
        self.hot: dict[str, dict] = {}
        self.cold: dict[str, dict] = {}

    def page_in(self, key: str, payload: dict) -> None:
        self.hot[key] = payload
        self.cold.pop(key, None)

    def page_out(self, key: str) -> None:
        if key in self.hot:
            self.cold[key] = {**self.hot[key], "tier": "cold"}
            del self.hot[key]

    def predict_and_preload(self, likely_keys: list[str]) -> list[str]:
        loaded = []
        for k in likely_keys:
            if k in self.cold:
                self.hot[k] = {**self.cold[k], "tier": "hot"}
                del self.cold[k]
                loaded.append(k)
        return loaded
