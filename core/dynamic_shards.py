from __future__ import annotations

import time


class DynamicCognitiveShards:
    """Dynamic shard loader/unloader with hot/cold state."""

    def __init__(self) -> None:
        self.shards: dict[str, dict] = {}

    def load(self, name: str, precision: str = "q5") -> dict:
        rec = {"name": name, "precision": precision, "state": "hot", "loaded_at": time.time(), "hits": 0}
        self.shards[name] = rec
        return rec

    def touch(self, name: str) -> None:
        if name in self.shards:
            self.shards[name]["hits"] += 1
            self.shards[name]["state"] = "hot"

    def cool_down(self) -> None:
        for rec in self.shards.values():
            if rec.get("hits", 0) < 2:
                rec["state"] = "cold"

    def unload_cold(self) -> list[str]:
        removed = [k for k, v in self.shards.items() if v.get("state") == "cold"]
        for k in removed:
            del self.shards[k]
        return removed
