from __future__ import annotations

import uvicorn

from aether_os.config.settings import SETTINGS
from aether_os.core.daemon import AetherDaemon
from aether_os.interface.terminal_ui import TerminalChat
from aether_os.interface.web_ui import create_app


def main() -> None:
    daemon = AetherDaemon()
    daemon.start()

    app = create_app(daemon)
    # Start web UI in a background thread handled by uvicorn.
    uvicorn.run(app, host=SETTINGS.web_host, port=SETTINGS.web_port)


if __name__ == "__main__":
    main()
