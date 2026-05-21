from __future__ import annotations


class ProactiveIntervention:
    """Score-based intervention system."""

    def __init__(self) -> None:
        self.proactivity_level = 5

    def threshold(self) -> int:
        return 10 - self.proactivity_level

    def score(self, context: dict) -> tuple[int, list[str]]:
        s = 0
        reasons: list[str] = []
        ram = context.get("ram_percent", 0)
        cpu = context.get("cpu_percent", 0)
        hour = context.get("time_context", {}).get("hour", 12)

        if ram > 95:
            s += 5
            reasons.append("RAM kritis >95%")
        elif ram > 85:
            s += 2
            reasons.append("RAM tinggi >85%")
        if cpu > 90:
            s += 3
            reasons.append("CPU tinggi >90%")
        if hour >= 23:
            s += 1
            reasons.append("Larut malam")
        return s, reasons

    def evaluate(self, context: dict) -> list[str]:
        s, reasons = self.score(context)
        if s > self.threshold():
            return [f"Intervensi proaktif (score={s}): {', '.join(reasons)}"]
        return []
