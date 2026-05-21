from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class MemoryEngine:
    """Persistent multi-type memory with vector recall."""

    MEMORY_TYPES = {"episodic", "identity", "semantic", "procedural", "knowledge"}

    def __init__(self, path: str, dim: int) -> None:
        self.path = Path(path)
        self.dim = dim
        self.records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            self.records = json.loads(self.path.read_text())

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.records, indent=2))

    def _embed(self, text: str) -> list[float]:
        arr = np.zeros(self.dim, dtype=np.float32)
        for i, ch in enumerate(text.encode("utf-8")):
            arr[i % self.dim] += ch / 255.0
        norm = np.linalg.norm(arr) or 1.0
        return (arr / norm).tolist()

    def add(self, text: str, memory_type: str = "episodic", metadata: dict[str, Any] | None = None) -> None:
        mtype = memory_type if memory_type in self.MEMORY_TYPES else "episodic"
        self.records.append(
            {"text": text, "type": mtype, "vec": self._embed(text), "metadata": metadata or {}}
        )
        self._save()

    def search(self, query: str, top_k: int = 3, memory_type: str | None = None) -> list[dict[str, Any]]:
        q = np.array(self._embed(query), dtype=np.float32)
        scored = []
        for rec in self.records:
            if memory_type and rec.get("type") != memory_type:
                continue
            v = np.array(rec["vec"], dtype=np.float32)
            scored.append((float(np.dot(q, v)), rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def stats(self) -> dict[str, int]:
        out = {k: 0 for k in self.MEMORY_TYPES}
        for r in self.records:
            out[r.get("type", "episodic")] = out.get(r.get("type", "episodic"), 0) + 1
        out["total"] = len(self.records)
        return out
