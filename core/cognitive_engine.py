from __future__ import annotations

from aether_os.ai.model_manager import ModelManager
from aether_os.core.web_access import WebAccessEngine


class CognitiveEngine:
    """5-mode specialist router: conversational/reasoning/coding/creative/knowledge."""

    def __init__(self, model_manager: ModelManager) -> None:
        self.model_manager = model_manager
        self.web_access = WebAccessEngine()

    def choose_specialist(self, message: str) -> str:
        m = message.lower()
        if any(k in m for k in ["python", "bug", "error", "api", "code"]):
            return "coding"
        if any(k in m for k in ["ide", "brainstorm", "what if", "cerita"]):
            return "creative"
        if any(k in m for k in ["apa itu", "definisi", "sejarah", "fakta"]):
            return "knowledge"
        if any(k in m for k in ["analisis", "kenapa", "strategi", "bandingkan"]):
            return "reasoning"
        return "conversational"

    def _extract_url(self, message: str) -> str | None:
        for token in message.split():
            if token.startswith("http://") or token.startswith("https://"):
                return token
        return None

    def respond(self, message: str) -> tuple[str, str]:
        specialist = self.choose_specialist(message)
        url = self._extract_url(message)
        web_context = ""
        if url:
            try:
                data = self.web_access.fetch(url)
                web_context = f" WEB[{data['status']}] {data['excerpt'][:280]}"
            except Exception as exc:
                web_context = f" WEB[error] {exc}"
        reply = self.model_manager.infer(message=f"{message}{web_context}", specialist=specialist)
        return specialist, reply
    def respond(self, message: str) -> tuple[str, str]:
        specialist = self.choose_specialist(message)
        return specialist, self.model_manager.infer(message=message, specialist=specialist)
