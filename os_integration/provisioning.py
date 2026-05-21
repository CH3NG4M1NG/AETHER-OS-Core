from __future__ import annotations

import os
from pathlib import Path


class ProvisioningManager:
    """Simulates baked-in OS provisioning at install/first boot."""

    def __init__(self, state_file: str = "./aether_provisioned.flag") -> None:
        self.state_file = Path(state_file)

    def provision_once(self) -> dict:
        if self.state_file.exists():
            return {"provisioned": True, "first_boot": False}

        os.environ.setdefault("AETHER_AUTOSTART", "1")
        os.environ.setdefault("AETHER_BUILTIN_APP", "enabled")
        os.environ.setdefault("AETHER_WEB_AGENT_ACCESS", "enabled")

        self.state_file.write_text("provisioned=true\n", encoding="utf-8")
        return {"provisioned": True, "first_boot": True}
