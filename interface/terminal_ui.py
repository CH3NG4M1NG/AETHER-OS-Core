from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt


class TerminalChat:
    def __init__(self, daemon) -> None:
        self.console = Console()
        self.daemon = daemon

    def run(self) -> None:
        self.console.print("[bold green]AETHER OS Terminal Chat[/bold green]")
        while True:
            msg = Prompt.ask("You")
            if msg.lower() in {"exit", "quit"}:
                break
            self.console.print(f"AETHER> {self.daemon.handle_message(msg)}")
