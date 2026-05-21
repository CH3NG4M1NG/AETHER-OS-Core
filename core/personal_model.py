from __future__ import annotations

from collections import Counter


class PersonalCognitiveModel:
    """Local-first, controllable user preference/profile model."""

    def __init__(self) -> None:
        self.intent_counter: Counter[str] = Counter()
        self.tool_counter: Counter[str] = Counter()

    def learn(self, intent: str, tool_hint: str = "") -> None:
        if intent:
            self.intent_counter[intent] += 1
        if tool_hint:
            self.tool_counter[tool_hint] += 1

    def profile(self) -> dict:
        return {
            "top_intents": self.intent_counter.most_common(5),
            "top_tools": self.tool_counter.most_common(5),
        }
