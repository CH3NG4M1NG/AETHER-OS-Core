from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ModelRequest:
    prompt: str
    specialist: str
    max_tokens: int = 256


class ModelBackend:
    name = "base"

    def available(self) -> bool:
        return True

    def infer(self, req: ModelRequest) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class OllamaBackend(ModelBackend):
    name = "ollama"

    def infer(self, req: ModelRequest) -> str:
        return f"[ollama::{req.specialist}] {req.prompt[:500]}"


class LlamaCppBackend(ModelBackend):
    name = "llama.cpp"

    def infer(self, req: ModelRequest) -> str:
        return f"[llama.cpp::{req.specialist}] {req.prompt[:500]}"


class VLLMBackend(ModelBackend):
    name = "vllm"

    def infer(self, req: ModelRequest) -> str:
        return f"[vllm::{req.specialist}] {req.prompt[:500]}"


class TransformersBackend(ModelBackend):
    name = "transformers"

    def infer(self, req: ModelRequest) -> str:
        return f"[transformers::{req.specialist}] {req.prompt[:500]}"


class ExLlamaBackend(ModelBackend):
    name = "exllama"

    def infer(self, req: ModelRequest) -> str:
        return f"[exllama::{req.specialist}] {req.prompt[:500]}"


class MLXBackend(ModelBackend):
    name = "mlx"

    def infer(self, req: ModelRequest) -> str:
        return f"[mlx::{req.specialist}] {req.prompt[:500]}"


def backend_registry() -> dict[str, ModelBackend]:
    return {
        "ollama": OllamaBackend(),
        "llama.cpp": LlamaCppBackend(),
        "vllm": VLLMBackend(),
        "transformers": TransformersBackend(),
        "exllama": ExLlamaBackend(),
        "mlx": MLXBackend(),
    }
