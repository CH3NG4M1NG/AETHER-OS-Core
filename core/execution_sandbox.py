from __future__ import annotations

import subprocess


class AINativeExecutionSandbox:
    """Safe-ish command sandbox wrapper with explicit allowlist."""

    ALLOW_PREFIX = ("python3", "pytest", "echo", "ls", "cat")

    def run(self, cmd: str) -> dict:
        if not cmd.strip().startswith(self.ALLOW_PREFIX):
            return {"ok": False, "error": "command_not_allowed"}
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {"ok": proc.returncode == 0, "code": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
