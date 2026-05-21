from __future__ import annotations

from aether_os.core.unified_runtime import UnifiedAIRuntimeManager


class ModelManager:
    """Compatibility facade over UnifiedAIRuntimeManager."""

    def __init__(self, gpu_enabled: bool = True) -> None:
        self.gpu_enabled = gpu_enabled
        self.runtime = UnifiedAIRuntimeManager()

    def ensure_models(self) -> list[str]:
        installed = self.runtime.ensure_required_models_installed()
        return [f"ready_backend:{name}" for name in self.runtime.enabled_backends] + [f"installed:{m}" for m in installed]
        return [f"ready_backend:{name}" for name in self.runtime.enabled_backends]
import os
import random


class ModelManager:
    """Model orchestration with dynamic switching and basic GPU policy."""

    def __init__(self, gpu_enabled: bool = True) -> None:
        self.gpu_enabled = gpu_enabled
        self.models = {
            "conversational": "aether-chat-q4",
            "reasoning": "aether-reason-q5",
            "coding": "aether-code-q5",
            "creative": "aether-creative-q4",
            "knowledge": "aether-knowledge-q5",
        }
        self.loaded_model: str | None = None

    def ensure_models(self) -> list[str]:
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        os.environ.setdefault("OLLAMA_GPU_LAYERS", "35")
        return [f"ready:{name}" for name in self.models.values()]

    def runtime_mode(self) -> str:
        return "hybrid-cpu-gpu" if self.gpu_enabled else "cpu-only"

    def infer(self, message: str, specialist: str, ram_percent: float = 0.0, vram_percent: float = 0.0) -> str:
        return self.runtime.infer(
            prompt=message,
            specialist=specialist,
            ram_percent=ram_percent,
            vram_percent=vram_percent,
            intent=specialist,
        )
    def switch_model(self, specialist: str) -> str:
        model = self.models.get(specialist, self.models["conversational"])
        self.loaded_model = model
        return model

    def infer(self, message: str, specialist: str) -> str:
        model = self.switch_model(specialist)
        token = random.randint(1000, 9999)
        return f"[{specialist}|{model}|{self.runtime_mode()}|{token}] {message}"
