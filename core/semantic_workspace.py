from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SemanticWorkspaceEngine:
    def __init__(self, state_path: str = "./aether_workspace_state.json") -> None:
        self.state_path = Path(state_path)
        self.graph: dict[str, dict[str, Any]] = {}
        self.active_workspace: str | None = None
        self.snapshots: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.state_path.exists():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.graph = data.get("graph", {})
            self.active_workspace = data.get("active_workspace")
            self.snapshots = data.get("snapshots", [])[-100:]

    def _save(self) -> None:
        self.state_path.write_text(json.dumps({"graph": self.graph, "active_workspace": self.active_workspace, "snapshots": self.snapshots[-100:]}, indent=2), encoding="utf-8")

    def activate_workspace(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        node = self.graph.setdefault(workspace_id, {"repos": [], "files": [], "docs": [], "tabs": [], "terminals": [], "ai_context": {}, "edges": []})
        for k, v in payload.items():
            if isinstance(node.get(k), list) and isinstance(v, list):
                node[k] = list(dict.fromkeys(node[k] + v))
            else:
                node[k] = v
        self.active_workspace = workspace_id
        self._save()
        return node

    def link_entities(self, workspace_id: str, source: str, target: str, relation: str) -> None:
        node = self.graph.setdefault(workspace_id, {"edges": []})
        node.setdefault("edges", []).append({"source": source, "target": target, "relation": relation, "ts": time.time()})
        self._save()

    def snapshot(self, context: dict[str, Any], intent: str) -> dict[str, Any]:
        snap = {"ts": time.time(), "active_workspace": self.active_workspace, "intent": intent, "context": context}
        self.snapshots.append(snap)
        self._save()
        return snap

    def status(self) -> dict[str, Any]:
        return {"active_workspace": self.active_workspace, "workspace_count": len(self.graph), "snapshot_count": len(self.snapshots)}
