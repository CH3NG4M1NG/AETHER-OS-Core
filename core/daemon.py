from __future__ import annotations

import threading
import time
from collections import deque

from aether_os.ai.model_manager import ModelManager
from aether_os.ai.proactive import ProactiveIntervention
from aether_os.config.settings import SETTINGS
from aether_os.core.agi_foundation import AGIFoundation
from aether_os.core.cognitive_engine import CognitiveEngine
from aether_os.core.context_engine import ContextEngine
from aether_os.core.memory_engine import MemoryEngine
from aether_os.core.voice_engine import VoiceEngine
from aether_os.core.semantic_workspace import SemanticWorkspaceEngine
from aether_os.core.cognitive_fs import CognitiveFileSystemLayer
from aether_os.core.intent_engine import IntentEngine
from aether_os.core.task_graph import CognitiveTaskGraphEngine
from aether_os.core.dynamic_shards import DynamicCognitiveShards
from aether_os.core.ai_virtual_memory import AIVirtualMemorySystem
from aether_os.core.personal_model import PersonalCognitiveModel
from aether_os.core.execution_sandbox import AINativeExecutionSandbox
from aether_os.core.phase4_ecosystem import UniversalCognitiveFabric, LiveWorldModel, PredictiveComputationEngine, PersistentAgentRegistry
from aether_os.core.phase5_mesh import UniversalCognitiveMesh, UniversalSemanticMemory, CognitiveComputeMarketplace, CognitiveDigitalTwin, CollectiveIntelligence
from aether_os.core.cognitive_engine import CognitiveEngine
from aether_os.core.context_engine import ContextEngine
from aether_os.core.memory_engine import MemoryEngine
from aether_os.os_integration.monitor import process_monitor
from aether_os.os_integration.provisioning import ProvisioningManager
from aether_os.security.anomaly import threat_assessment


class AetherDaemon:
    def __init__(self) -> None:
        self.memory_engine = MemoryEngine(path=SETTINGS.memory_path, dim=SETTINGS.vector_dim)
        self.context_engine = ContextEngine()
        self.model_manager = ModelManager(gpu_enabled=SETTINGS.gpu_preferred)
        self.cognitive_engine = CognitiveEngine(self.model_manager)
        self.proactive = ProactiveIntervention()
        self.agi_foundation = AGIFoundation(self.memory_engine)
        self.provisioning = ProvisioningManager()
        self.voice_engine = VoiceEngine()
        self.workspace_engine = SemanticWorkspaceEngine()
        self.cognitive_fs = CognitiveFileSystemLayer()
        self.intent_engine = IntentEngine()
        self.task_graph = CognitiveTaskGraphEngine()
        self.shards = DynamicCognitiveShards()
        self.ai_vm = AIVirtualMemorySystem()
        self.personal_model = PersonalCognitiveModel()
        self.sandbox = AINativeExecutionSandbox()
        self.fabric = UniversalCognitiveFabric()
        self.world_model = LiveWorldModel()
        self.predictive = PredictiveComputationEngine()
        self.agent_registry = PersistentAgentRegistry()
        self.mesh = UniversalCognitiveMesh()
        self.semantic_memory = UniversalSemanticMemory()
        self.compute_market = CognitiveComputeMarketplace()
        self.digital_twin = CognitiveDigitalTwin()
        self.collective = CollectiveIntelligence()
        self.provisioning = ProvisioningManager()
        self.running = False
        self.notifications: deque[dict] = deque(maxlen=100)

    def handle_message(self, message: str) -> str:
        intent = self.intent_engine.detect(self.context_engine.snapshot(), hint=message)
        specialist, reply = self.cognitive_engine.respond(message)
        self.model_manager.runtime.memory.record_session({"intent": intent, "message": message})
        self.personal_model.learn(intent=intent, tool_hint="chat")
        self.task_graph.add_task(f"chat:{len(self.notifications)}", kind="chat", metadata={"intent": intent})
        self.agent_registry.upsert("coding-agent", role="persistent_assistant", workspace=self.workspace_engine.active_workspace)
        next_mods = self.predictive.predict_next_modules(intent)
        shard = self.shards.load(intent if intent != "general" else "reasoning")
        self.ai_vm.predict_and_preload(next_mods)
        self.ai_vm.page_in(shard["name"], {"precision": shard["precision"], "type": "expert_module"})
        self.semantic_memory.federate("local-chat", "episodic", message[:300])
        self.collective.share_pattern(f"intent:{intent}", source="local")
        shard = self.shards.load(intent if intent != "general" else "reasoning")
        self.ai_vm.page_in(shard["name"], {"precision": shard["precision"], "type": "expert_module"})
        specialist, reply = self.cognitive_engine.respond(message)
        self.memory_engine.add(message, memory_type="episodic", metadata={"source": "user"})
        self.memory_engine.add(reply, memory_type="episodic", metadata={"source": "assistant", "specialist": specialist})
        return reply

    def built_in_app_state(self) -> dict:
        return {
            "name": SETTINGS.built_in_app_name,
            "ready": self.running,
            "agi": self.agi_foundation.status(),
            "runtime": self.model_manager.runtime.observability(),
            "workspace": self.workspace_engine.status(),
            "phase3": {"task_graph": self.task_graph.status(), "shards": self.shards.shards, "ai_vm": {"hot": len(self.ai_vm.hot), "cold": len(self.ai_vm.cold)}, "personal": self.personal_model.profile()},
            "phase4": {"fabric_nodes": self.fabric.nodes, "world_projects": self.world_model.projects, "agents": self.agent_registry.agents},
            "phase5": {"mesh_nodes": self.mesh.nodes, "mesh_routes": len(self.mesh.routes), "federated_memories": len(self.semantic_memory.records), "market_providers": len(self.compute_market.providers), "twins": len(self.digital_twin.twins), "collective_patterns": len(self.collective.patterns)},
        }
        }
        }
        }
        }
        }
        return {"name": SETTINGS.built_in_app_name, "ready": self.running}

    def _push_notification(self, level: str, message: str) -> None:
        self.notifications.appendleft({"level": level, "message": message, "ts": time.time()})

    def observe_loop(self) -> None:
        while self.running:
            ctx = self.context_engine.snapshot()
            agi_cycle = self.agi_foundation.cycle(ctx)
            intent = self.intent_engine.detect(ctx)
            self.model_manager.runtime.memory.put_context("latest_system", ctx)
            snap = self.workspace_engine.snapshot(ctx, intent=intent)
            if self.workspace_engine.active_workspace:
                self.world_model.update_project(self.workspace_engine.active_workspace, {"latest_snapshot": snap, "intent": intent})
            self.workspace_engine.snapshot(ctx, intent=intent)
            self.shards.cool_down()
            for n in self.proactive.evaluate(ctx):
                self._push_notification("info", n)
            self._push_notification("agi", f"cycle plan: {agi_cycle['plan']}")
            for n in self.proactive.evaluate(ctx):
                self._push_notification("info", n)
            self._push_notification("agi", f"cycle plan: {agi_cycle['plan']}")
            self.model_manager.runtime.memory.put_context("latest_system", ctx)
            for n in self.proactive.evaluate(ctx):
                self._push_notification("info", n)
            self._push_notification("agi", f"cycle plan: {agi_cycle['plan']}")
            for n in self.proactive.evaluate(ctx):
                self._push_notification("info", n)
            self._push_notification("agi", f"cycle plan: {agi_cycle['plan']}")
            for n in self.proactive.evaluate(ctx):
                self._push_notification("info", n)
            time.sleep(30)

    def security_loop(self) -> None:
        while self.running:
            ctx = self.context_engine.snapshot()
            threat = threat_assessment(ctx)
            if threat in {"high", "critical"}:
                self._push_notification("security", f"Threat level: {threat}")
            time.sleep(120)

    def dream_cycle(self) -> None:
        while self.running:
            ctx = self.context_engine.snapshot()
            if ctx.get("activity") == "idle":
                self.memory_engine.add("Dream consolidation cycle", memory_type="semantic", metadata={"source": "dream"})
            time.sleep(3600)

    def health_loop(self) -> None:
        while self.running:
            _ = process_monitor()
            time.sleep(120)

    def start(self) -> None:
        self.model_manager.ensure_models()
        if SETTINGS.autoprovision_on_boot:
            status = self.provisioning.provision_once()
            if status.get("first_boot"):
                self._push_notification("system", "AETHER provisioned during OS install/first boot")
        self.running = True
        threading.Thread(target=self.observe_loop, daemon=True).start()
        threading.Thread(target=self.security_loop, daemon=True).start()
        threading.Thread(target=self.dream_cycle, daemon=True).start()
        threading.Thread(target=self.health_loop, daemon=True).start()
