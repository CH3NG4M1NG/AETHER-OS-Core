from __future__ import annotations


def detect_behavioral_anomaly(context: dict) -> bool:
    return context.get("cpu_percent", 0) > 95 and context.get("ram_percent", 0) > 90


def threat_assessment(context: dict) -> str:
    if detect_behavioral_anomaly(context):
        return "high"
    if context.get("cpu_percent", 0) > 85:
        return "medium"
    return "low"
