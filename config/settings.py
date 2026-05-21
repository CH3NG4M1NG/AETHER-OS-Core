from dataclasses import dataclass, field
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    vector_dim: int = 256
    memory_path: str = "./aether_memory.json"
    web_host: str = "127.0.0.1"
    web_port: int = 8080
    gpu_preferred: bool = True
    autoprovision_on_boot: bool = True
    built_in_app_name: str = "AETHER Console"
    local_first_mode: bool = True
    inference_tick_seconds: int = 5
    runtime_targets: list[str] = field(default_factory=lambda: ["ollama", "llama.cpp", "vllm", "transformers", "exllama", "mlx"])


SETTINGS = Settings()
