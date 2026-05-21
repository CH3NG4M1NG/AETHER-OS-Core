from __future__ import annotations

import datetime as dt
import platform
import time

import psutil


class ContextEngine:
    """System awareness including activity and time context."""

    def _classify_activity(self, cpu: float) -> str:
        if cpu > 70:
            return "high-load"
        if cpu > 25:
            return "active"
        return "idle"

    def snapshot(self) -> dict:
        now = dt.datetime.now()
        cpu = psutil.cpu_percent(interval=0.1)
        return {
            "ts": time.time(),
            "platform": platform.platform(),
            "cpu_percent": cpu,
            "ram_percent": psutil.virtual_memory().percent,
            "active_procs": len(psutil.pids()),
            "time_context": {
                "hour": now.hour,
                "weekday": now.weekday(),
                "is_weekend": now.weekday() >= 5,
            },
            "activity": self._classify_activity(cpu),
        }
