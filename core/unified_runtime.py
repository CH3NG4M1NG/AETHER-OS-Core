from __future__ import annotations

import time
from collections import deque

from aether_os.config.settings import SETTINGS
from aether_os.core.model_abstraction import ModelRequest, backend_registry
from aether_os.core.phase4_ecosystem import SelfEvolvingRuntime, AutonomousOptimizationEngine


class SmartQuantizationEngine:
    def choose_precision(self, ram_percent: float, vram_percent: float) -> str:
        pressure = max(ram_percent, vram_percent)
        if pressure > 90:
            return "q4"
        if pressure > 75:
            return "q5"
        return "fp16"


class AIAwareResourceScheduler:
    def pick_priority(self, intent: str) -> int:
        mapping = {"coding": 100, "reasoning": 90, "knowledge": 80, "creative": 70, "background": 20}
        return mapping.get(intent, 50)


class CognitiveMemoryManager:
    def __init__(self) -> None:
        self.embedding_cache: dict[str, list[float]] = {}
        self.context_cache: dict[str, dict] = {}
        self.semantic_sessions: deque[dict] = deque(maxlen=200)
        self.active_workspaces: dict[str, dict] = {}

    def put_context(self, key: str, context: dict) -> None:
        self.context_cache[key] = context

    def record_session(self, session_item: dict) -> None:
        self.semantic_sessions.appendleft(session_item)

    def activate_workspace(self, workspace_id: str, payload: dict) -> None:
        self.active_workspaces[workspace_id] = payload


class UnifiedAIRuntimeManager:
    """System runtime orchestrator for model lifecycle, scheduling, memory and precision policy."""

    def __init__(self) -> None:
        self.backends = backend_registry()
        self.enabled_backends = [b for b in SETTINGS.runtime_targets if b in self.backends]
        self.quant = SmartQuantizationEngine()
        self.scheduler = AIAwareResourceScheduler()
        self.memory = CognitiveMemoryManager()
        self.loaded_models: dict[str, dict] = {}
        self.last_inference_meta: dict = {}
        self.installed_models: set[str] = set()
        self.self_evolving = SelfEvolvingRuntime()
        self.optimizer = AutonomousOptimizationEngine()

    def install_model(self, specialist: str, backend: str, precision: str) -> str:
        model_id = f"{backend}:{specialist}:{precision}"
        self.installed_models.add(model_id)
        return model_id

    def ensure_required_models_installed(self) -> list[str]:
        required = ["conversational", "reasoning", "coding", "creative", "knowledge"]
        installed = []
        backend = self.select_backend()
        for spec in required:
            installed.append(self.install_model(spec, backend, "q5"))
        return installed

    def load_model(self, specialist: str, backend: str, precision: str) -> dict:
        model_id = f"{backend}:{specialist}:{precision}"
        self.loaded_models[specialist] = {"model_id": model_id, "backend": backend, "precision": precision, "loaded_at": time.time()}
        return self.loaded_models[specialist]

    def unload_model(self, specialist: str) -> None:
        self.loaded_models.pop(specialist, None)

    def select_backend(self) -> str:
        for name in self.enabled_backends:
            if self.backends[name].available():
                return name
        return "ollama"

    def infer(self, prompt: str, specialist: str, ram_percent: float = 0, vram_percent: float = 0, intent: str = "background") -> str:
        backend_name = self.select_backend()
        precision = self.quant.choose_precision(ram_percent, vram_percent)
        self.install_model(specialist=specialist, backend=backend_name, precision=precision)
        self.load_model(specialist=specialist, backend=backend_name, precision=precision)
        priority = self.scheduler.pick_priority(intent=intent)
        req = ModelRequest(prompt=prompt, specialist=specialist)
        text = self.backends[backend_name].infer(req)
        self.self_evolving.observe(backend_name, precision, intent)
        self.last_inference_meta = {
            "backend": backend_name,
            "precision": precision,
            "priority": priority,
            "ram_percent": ram_percent,
            "vram_percent": vram_percent,
            "specialist": specialist,
        }
        return text

    def observability(self) -> dict:
        return {
            "active_backends": self.enabled_backends,
            "loaded_models": self.loaded_models,
            "last_inference": self.last_inference_meta,
            "installed_models": sorted(self.installed_models),
            "self_evolving_policy": self.self_evolving.policy,
            "optimizer_recommendation": self.optimizer.recommend(self.loaded_models and {"loaded_models": self.loaded_models} or {}),
            "cache": {
                "embeddings": len(self.memory.embedding_cache),
                "contexts": len(self.memory.context_cache),
                "sessions": len(self.memory.semantic_sessions),
                "workspaces": len(self.memory.active_workspaces),
            },
        }
