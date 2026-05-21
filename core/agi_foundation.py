from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AGIState:
    identity: str = "AETHER"
    role: str = "AI embodied in OS runtime"
    goals: list[str] = field(default_factory=lambda: [
        "Maintain system stability",
        "Preserve long-term memory coherence",
        "Assist user tasks proactively",
    ])
    last_cycle_ts: float = 0.0
    last_plan: str = ""


class AGIFoundation:
    """Perceive→Think→Act loop that treats OS as the AI embodiment substrate."""

    def __init__(self, memory_engine) -> None:
        self.memory_engine = memory_engine
        self.state = AGIState()

    def perceive(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "activity": context.get("activity"),
            "cpu": context.get("cpu_percent", 0),
            "ram": context.get("ram_percent", 0),
            "hour": context.get("time_context", {}).get("hour", 0),
        }

    def think(self, perception: dict[str, Any]) -> str:
        if perception["ram"] > 90:
            return "Prioritise memory pressure mitigation and reduce non-critical workloads"
        if perception["cpu"] > 85:
            return "Shift background cognition to low-impact mode"
        if perception["activity"] == "idle":
            return "Run learning consolidation and memory indexing"
        return "Stay assistive with balanced foreground/background cognition"

    def act(self, plan: str) -> dict[str, Any]:
        self.state.last_cycle_ts = time.time()
        self.state.last_plan = plan
        self.memory_engine.add(
            text=f"AGI cycle plan: {plan}",
            memory_type="procedural",
            metadata={"source": "agi_foundation", "ts": self.state.last_cycle_ts},
        )
        return {"plan": plan, "executed": True, "ts": self.state.last_cycle_ts}

    def cycle(self, context: dict[str, Any]) -> dict[str, Any]:
        perception = self.perceive(context)
        plan = self.think(perception)
        return self.act(plan)

    def status(self) -> dict[str, Any]:
        return {
            "identity": self.state.identity,
            "role": self.state.role,
            "goals": self.state.goals,
            "last_cycle_ts": self.state.last_cycle_ts,
            "last_plan": self.state.last_plan,
        }
