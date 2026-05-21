from __future__ import annotations

import time


class UniversalCognitiveMesh:
    """Federated cognition mesh registry across devices/nodes."""

    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.routes: list[dict] = []

    def join(self, node_id: str, role: str, locality: str = "local") -> dict:
        self.nodes[node_id] = {"role": role, "locality": locality, "joined_at": time.time()}
        return self.nodes[node_id]

    def route(self, task: str, from_node: str, to_node: str) -> dict:
        rec = {"task": task, "from": from_node, "to": to_node, "ts": time.time()}
        self.routes.append(rec)
        return rec


class UniversalSemanticMemory:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def federate(self, source: str, memory_type: str, summary: str) -> dict:
        rec = {"source": source, "memory_type": memory_type, "summary": summary, "ts": time.time()}
        self.records.append(rec)
        return rec


class CognitiveComputeMarketplace:
    def __init__(self) -> None:
        self.providers: dict[str, dict] = {}

    def register_provider(self, provider_id: str, capabilities: list[str], score: float = 1.0) -> dict:
        self.providers[provider_id] = {"capabilities": capabilities, "score": score, "ts": time.time()}
        return self.providers[provider_id]

    def match(self, need: str) -> list[dict]:
        out = []
        for pid, info in self.providers.items():
            if need in info.get("capabilities", []):
                out.append({"provider": pid, **info})
        return sorted(out, key=lambda x: x.get("score", 0), reverse=True)


class CognitiveDigitalTwin:
    def __init__(self) -> None:
        self.twins: dict[str, dict] = {}

    def update(self, user_id: str, workflow_model: dict, preferences: dict) -> dict:
        self.twins[user_id] = {"workflow_model": workflow_model, "preferences": preferences, "updated_at": time.time()}
        return self.twins[user_id]


class CollectiveIntelligence:
    def __init__(self) -> None:
        self.patterns: list[dict] = []

    def share_pattern(self, pattern: str, source: str) -> dict:
        rec = {"pattern": pattern, "source": source, "ts": time.time()}
        self.patterns.append(rec)
        return rec
