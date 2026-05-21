"""
AETHER Kernel Bridge
Komunikasi antara Python userspace dan kernel modules.
Tulis ke /proc/aether/control untuk kirim perintah ke kernel.
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict

log = logging.getLogger("aether.kernel_bridge")

PROC_AETHER         = "/proc/aether"
PROC_STATUS         = "/proc/aether/status"
PROC_CONTROL        = "/proc/aether/control"
PROC_MEMORY         = "/proc/aether/memory"
PROC_PROCESSES      = "/proc/aether/processes"
PROC_SCHED_STATUS   = "/proc/scheduler/status"
PROC_SCHED_CONTROL  = "/proc/scheduler/control"
PROC_MEM_STATUS     = "/proc/memory_mgr/status"
PROC_MEM_CONTROL    = "/proc/memory_mgr/control"


class AetherKernelBridge:
    """
    Bridge antara AETHER Python daemon dan kernel modules.
    Kalau kernel module tidak terload, fallback ke userspace-only mode.
    """

    def __init__(self):
        self.kernel_available = self._check_kernel_module()
        if self.kernel_available:
            log.info("Kernel modules detected — full kernel integration active")
        else:
            log.info("Kernel modules not loaded — userspace-only mode")

    def _check_kernel_module(self) -> bool:
        return os.path.exists(PROC_AETHER)

    def _write_proc(self, path: str, command: str) -> bool:
        try:
            with open(path, 'w') as f:
                f.write(command + "\n")
            return True
        except (PermissionError, FileNotFoundError, OSError) as e:
            log.debug(f"proc write failed {path}: {e}")
            return False

    def _read_proc(self, path: str) -> Optional[Dict]:
        try:
            with open(path, 'r') as f:
                content = f.read()
            result = {}
            for line in content.strip().split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    result[k.strip()] = v.strip()
            return result
        except Exception as e:
            log.debug(f"proc read failed {path}: {e}")
            return None

    # ── Cognitive Engine ──

    def set_mode(self, mode: str) -> bool:
        """Beritahu kernel mode kognitif saat ini."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_CONTROL, f"mode:{mode}")

    def report_inference_done(self) -> bool:
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_CONTROL, "inference_done")

    def set_memory_pressure(self, pressure: int) -> bool:
        """pressure: 0-100"""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_CONTROL, f"pressure:{pressure}")

    def set_cognitive_load(self, load: int) -> bool:
        """load: 0-100"""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_CONTROL, f"load:{load}")

    def get_status(self) -> Dict:
        if not self.kernel_available:
            return {"kernel_available": False}
        data = self._read_proc(PROC_STATUS) or {}
        data["kernel_available"] = True
        return data

    def get_memory_info(self) -> Dict:
        if not self.kernel_available:
            return {}
        return self._read_proc(PROC_MEMORY) or {}

    # ── Scheduler ──

    def notify_ai_start(self, pid: int) -> bool:
        """Beritahu kernel bahwa AI inference dimulai."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_SCHED_CONTROL, f"ai_start:{pid}")

    def notify_ai_stop(self) -> bool:
        """Beritahu kernel bahwa AI inference selesai."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_SCHED_CONTROL, "ai_stop")

    def register_process(self, pid: int, proc_type: int,
                         nice_delta: int = 0) -> bool:
        """Register proses dengan scheduler AETHER."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_SCHED_CONTROL,
                                f"register:{pid}:{proc_type}:{nice_delta}")

    def scan_for_games(self) -> bool:
        """Trigger gaming mode detection di kernel."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_SCHED_CONTROL, "scan_gaming")

    def get_scheduler_status(self) -> Dict:
        if not self.kernel_available:
            return {}
        return self._read_proc(PROC_SCHED_STATUS) or {}

    # ── Memory Manager ──

    def register_hot_region(self, pid: int, size_kb: int,
                            label: str = "model") -> bool:
        """Daftarkan region memori HOT (jangan swap!)."""
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_MEM_CONTROL,
                                f"register_hot:{pid}:{size_kb}:{label}")

    def notify_pressure(self, pressure: int) -> bool:
        if not self.kernel_available:
            return False
        return self._write_proc(PROC_MEM_CONTROL, f"pressure:{pressure}")

    def get_memory_status(self) -> Dict:
        if not self.kernel_available:
            return {}
        return self._read_proc(PROC_MEM_STATUS) or {}

    # ── High Level Helpers ──

    def on_inference_start(self, pid: int, model_size_mb: int):
        """Call ini saat AETHER mulai inference."""
        self.notify_ai_start(pid)
        self.set_mode("reasoning")
        if model_size_mb > 0:
            self.register_hot_region(pid, model_size_mb * 1024, "ai_model")
        log.debug(f"Kernel: inference start pid={pid} model={model_size_mb}MB")

    def on_inference_done(self, pid: int):
        """Call ini saat inference selesai."""
        self.notify_ai_stop()
        self.report_inference_done()
        self.set_mode("idle")
        log.debug(f"Kernel: inference done pid={pid}")

    def on_gaming_check(self):
        """Periodic gaming detection."""
        self.scan_for_games()
        status = self.get_scheduler_status()
        return status.get("gaming_mode") == "1"

    def full_status(self) -> Dict:
        """Status lengkap semua kernel modules."""
        return {
            "kernel_available": self.kernel_available,
            "cognitive": self.get_status(),
            "scheduler": self.get_scheduler_status(),
            "memory": self.get_memory_status()
        }


# Singleton
_bridge = None

def get_bridge() -> AetherKernelBridge:
    global _bridge
    if _bridge is None:
        _bridge = AetherKernelBridge()
    return _bridge


if __name__ == "__main__":
    print("[AETHER] Testing Kernel Bridge...")
    bridge = AetherKernelBridge()
    print(f"Kernel available: {bridge.kernel_available}")
    if bridge.kernel_available:
        print(f"Status: {bridge.get_status()}")
        print(f"Memory: {bridge.get_memory_info()}")
        print(f"Scheduler: {bridge.get_scheduler_status()}")
    else:
        print("Running in userspace-only mode (kernel modules not loaded)")
    print("[AETHER] Kernel Bridge OK ✓")
