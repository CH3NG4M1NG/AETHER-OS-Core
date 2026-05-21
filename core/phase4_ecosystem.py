from __future__ import annotations

import time
from collections import defaultdict


class SelfEvolvingRuntime:
    """Learns runtime policy from local usage and updates preferred strategies."""

    def __init__(self) -> None:
        self.stats = defaultdict(int)
        self.policy = {"preferred_precision": "q5", "preferred_backend": "ollama"}

    def observe(self, backend: str, precision: str, intent: str) -> None:
        self.stats[f"backend:{backend}"] += 1
        self.stats[f"precision:{precision}"] += 1
        self.stats[f"intent:{intent}"] += 1
        if self.stats[f"precision:fp16"] > self.stats[f"precision:q4"]:
            self.policy["preferred_precision"] = "fp16"
        self.policy["preferred_backend"] = backend


class UniversalCognitiveFabric:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}

    def register_node(self, node_id: str, role: str, capabilities: list[str]) -> dict:
        self.nodes[node_id] = {"role": role, "capabilities": capabilities, "ts": time.time()}
        return self.nodes[node_id]


class LiveWorldModel:
    def __init__(self) -> None:
        self.projects: dict[str, dict] = {}

    def update_project(self, project_id: str, topology: dict) -> dict:
        self.projects[project_id] = {"topology": topology, "updated_at": time.time()}
        return self.projects[project_id]


class AutonomousOptimizationEngine:
    def recommend(self, observability: dict) -> dict:
        loaded = observability.get("loaded_models", {})
        if len(loaded) > 3:
            return {"action": "unload_idle_models", "reason": "too_many_loaded_models"}
        return {"action": "keep_current_topology", "reason": "stable"}


class PredictiveComputationEngine:
    def predict_next_modules(self, intent: str) -> list[str]:
        mapping = {
            "coding": ["reasoning", "coding", "knowledge"],
            "research": ["knowledge", "reasoning"],
            "rendering": ["planning"],
            "streaming": ["ui"],
        }
        return mapping.get(intent, ["reasoning"])


class PersistentAgentRegistry:
    def __init__(self) -> None:
        self.agents: dict[str, dict] = {}

    def upsert(self, agent_id: str, role: str, workspace: str | None = None) -> dict:
        self.agents[agent_id] = {"role": role, "workspace": workspace, "updated_at": time.time()}
        return self.agents[agent_id]
