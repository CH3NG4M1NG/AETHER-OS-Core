from __future__ import annotations

import time


class CognitiveTaskGraphEngine:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def add_task(self, task_id: str, kind: str, metadata: dict | None = None) -> dict:
        self.nodes[task_id] = {"kind": kind, "metadata": metadata or {}, "ts": time.time()}
        return self.nodes[task_id]

    def link(self, src: str, dst: str, relation: str = "depends_on") -> dict:
        edge = {"src": src, "dst": dst, "relation": relation, "ts": time.time()}
        self.edges.append(edge)
        return edge

    def status(self) -> dict:
        return {"tasks": len(self.nodes), "links": len(self.edges)}
