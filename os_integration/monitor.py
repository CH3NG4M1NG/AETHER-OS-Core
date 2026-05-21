from __future__ import annotations

import psutil


def process_monitor() -> list[dict]:
    top = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        info = p.info
        top.append(info)
    top.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    return top[:10]


def ram_optimizer() -> dict:
    vm = psutil.virtual_memory()
    return {
        "ram_used_percent": vm.percent,
        "recommendation": "drop caches/manual review" if vm.percent > 85 else "healthy",
    }
