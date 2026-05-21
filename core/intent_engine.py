from __future__ import annotations


class IntentEngine:
    def detect(self, context: dict, hint: str = "") -> str:
        h = hint.lower()
        if any(k in h for k in ["code", "python", "repo", "bug", "debug"]):
            return "coding"
        if any(k in h for k in ["blender", "render", "gpu"]):
            return "rendering"
        if any(k in h for k in ["research", "docs", "browser"]):
            return "research"
        if any(k in h for k in ["stream", "obs", "mic"]):
            return "streaming"
        return "background" if context.get("activity") == "idle" else "general"
