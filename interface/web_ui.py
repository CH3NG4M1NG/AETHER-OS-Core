from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def create_app(daemon) -> FastAPI:
    app = FastAPI(title="AETHER OS")

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return """
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>AETHER OS Console</title>
<style>
body { font-family: Inter, system-ui, sans-serif; background: radial-gradient(circle at top, #1f2440, #0b0f1a); color:#e7ecff; margin:0; }
.wrap { max-width: 980px; margin: 24px auto; padding: 20px; }
.card { background: rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 16px; margin-bottom: 16px; }
input, button { border-radius:10px; border:none; padding:10px 12px; }
input { width: 70%; }
button { background:#6c7bff; color:white; cursor:pointer; }
pre { white-space:pre-wrap; }
</style>
</head>
<body>
<div class='wrap'>
  <h1>🧠 AETHER OS — Embodied AGI Console</h1>
  <div class='card'><strong>Status</strong><pre id='status'>loading...</pre></div>
  <div class='card'>
    <strong>Chat + Voice</strong><br/><br/>
    <input id='msg' placeholder='Tanya AETHER...'/> <button onclick='sendMsg()'>Kirim</button>
    <button onclick='speakLast()'>🔊 Bicara</button>
    <pre id='chat'></pre>
  </div>
</div>
<script>
let lastReply = '';
async function refreshStatus(){
  const r = await fetch('/api/builtin-app');
  const j = await r.json();
  document.getElementById('status').textContent = JSON.stringify(j, null, 2);
}
async function sendMsg(){
  const msg = document.getElementById('msg').value;
  const r = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
  const j = await r.json();
  lastReply = j.reply || '';
  document.getElementById('chat').textContent += `\nYou: ${msg}\nAETHER: ${lastReply}\n`;
}
async function speakLast(){
  if(!lastReply) return;
  const r = await fetch('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:lastReply})});
  const j = await r.json();
  const audio = new Audio('data:audio/wav;base64,' + j.audio_base64);
  audio.play();
}
refreshStatus();
setInterval(refreshStatus, 5000);
</script>
</body>
</html>
        """

    @app.post("/api/chat")
    def chat(payload: dict) -> dict:
        text = payload.get("message", "")
        return {"reply": daemon.handle_message(text)}

    @app.get("/api/status")
    def status() -> dict:
        ctx = daemon.context_engine.snapshot()
        return {
            "status": "ok",
            "runtime_mode": daemon.model_manager.runtime_mode(),
            "activity": ctx.get("activity"),
            "cpu_percent": ctx.get("cpu_percent"),
            "ram_percent": ctx.get("ram_percent"),
        }

    @app.get("/api/notifications")
    def notifications() -> dict:
        return {"items": list(daemon.notifications)}

    @app.get("/api/memory/stats")
    def memory_stats() -> dict:
        return daemon.memory_engine.stats()

    @app.post("/api/memory/recall")
    def recall(payload: dict) -> dict:
        query = payload.get("query", "")
        memory_type = payload.get("type")
        top_k = int(payload.get("top_k", 3))
        return {"results": daemon.memory_engine.search(query, top_k=top_k, memory_type=memory_type)}

    @app.get("/api/builtin-app")
    def builtin_app() -> dict:
        return daemon.built_in_app_state()

    @app.post("/api/web/access")
    def web_access(payload: dict) -> dict:
        url = payload.get("url", "")
        return daemon.cognitive_engine.web_access.fetch(url)

    @app.get("/api/agi/status")
    def agi_status() -> dict:
        return daemon.agi_foundation.status()

    @app.post("/api/agi/goal")
    def agi_add_goal(payload: dict) -> dict:
        goal = str(payload.get("goal", "")).strip()
        if goal:
            daemon.agi_foundation.state.goals.append(goal)
        return daemon.agi_foundation.status()

    @app.post("/api/voice/speak")
    def voice_speak(payload: dict) -> dict:
        text = str(payload.get("text", "")).strip()
        return daemon.voice_engine.synthesize(text)

    @app.get("/api/runtime/observability")
    def runtime_observability() -> dict:
        return daemon.model_manager.runtime.observability()

    @app.post("/api/workspace/activate")
    def workspace_activate(payload: dict) -> dict:
        workspace_id = str(payload.get("workspace_id", "default")).strip()
        data = payload.get("data", {})
        daemon.model_manager.runtime.memory.activate_workspace(workspace_id, data)
        return {"ok": True, "workspace_id": workspace_id}

    @app.get("/api/intent/current")
    def intent_current() -> dict:
        ctx = daemon.context_engine.snapshot()
        return {"intent": daemon.intent_engine.detect(ctx), "activity": ctx.get("activity")}

    @app.post("/api/workspace/graph")
    def workspace_graph(payload: dict) -> dict:
        workspace_id = str(payload.get("workspace_id", "default")).strip()
        node = daemon.workspace_engine.activate_workspace(workspace_id, payload.get("data", {}))
        return {"workspace_id": workspace_id, "node": node}

    @app.post("/api/workspace/link")
    def workspace_link(payload: dict) -> dict:
        daemon.workspace_engine.link_entities(
            workspace_id=str(payload.get("workspace_id", "default")),
            source=str(payload.get("source", "")),
            target=str(payload.get("target", "")),
            relation=str(payload.get("relation", "related")),
        )
        return {"ok": True}

    @app.post("/api/cfs/index")
    def cfs_index(payload: dict) -> dict:
        return daemon.cognitive_fs.index_file(
            file_path=str(payload.get("path", "")),
            content=str(payload.get("content", "")),
            project=payload.get("project"),
        )

    @app.post("/api/cfs/search")
    def cfs_search(payload: dict) -> dict:
        return {"results": daemon.cognitive_fs.semantic_search(str(payload.get("query", "")))}

    @app.get("/api/phase3/shards")
    def phase3_shards() -> dict:
        return {"shards": daemon.shards.shards}

    @app.post("/api/phase3/shards/unload-cold")
    def phase3_unload_cold() -> dict:
        return {"unloaded": daemon.shards.unload_cold()}

    @app.get("/api/phase3/task-graph")
    def phase3_task_graph() -> dict:
        return {"status": daemon.task_graph.status(), "nodes": daemon.task_graph.nodes, "edges": daemon.task_graph.edges}

    @app.get("/api/phase3/personal-profile")
    def phase3_profile() -> dict:
        return daemon.personal_model.profile()

    @app.post("/api/phase3/sandbox/run")
    def phase3_sandbox_run(payload: dict) -> dict:
        return daemon.sandbox.run(str(payload.get("cmd", "")))

    @app.post("/api/phase4/fabric/register")
    def phase4_fabric_register(payload: dict) -> dict:
        return daemon.fabric.register_node(
            node_id=str(payload.get("node_id", "local-node")),
            role=str(payload.get("role", "local")),
            capabilities=payload.get("capabilities", ["reasoning"]),
        )

    @app.post("/api/phase4/world/update")
    def phase4_world_update(payload: dict) -> dict:
        return daemon.world_model.update_project(
            project_id=str(payload.get("project_id", "default")),
            topology=payload.get("topology", {}),
        )

    @app.get("/api/phase4/agents")
    def phase4_agents() -> dict:
        return {"agents": daemon.agent_registry.agents}

    @app.get("/api/phase4/self-evolving")
    def phase4_self_evolving() -> dict:
        return {
            "policy": daemon.model_manager.runtime.self_evolving.policy,
            "installed_models": sorted(daemon.model_manager.runtime.installed_models),
        }

    @app.post("/api/phase5/mesh/join")
    def phase5_mesh_join(payload: dict) -> dict:
        return daemon.mesh.join(
            node_id=str(payload.get("node_id", "local-node")),
            role=str(payload.get("role", "general")),
            locality=str(payload.get("locality", "local")),
        )

    @app.post("/api/phase5/mesh/route")
    def phase5_mesh_route(payload: dict) -> dict:
        return daemon.mesh.route(
            task=str(payload.get("task", "reasoning")),
            from_node=str(payload.get("from_node", "local-node")),
            to_node=str(payload.get("to_node", "peer-node")),
        )

    @app.post("/api/phase5/memory/federate")
    def phase5_memory_federate(payload: dict) -> dict:
        return daemon.semantic_memory.federate(
            source=str(payload.get("source", "local")),
            memory_type=str(payload.get("memory_type", "semantic")),
            summary=str(payload.get("summary", "")),
        )

    @app.post("/api/phase5/market/register")
    def phase5_market_register(payload: dict) -> dict:
        return daemon.compute_market.register_provider(
            provider_id=str(payload.get("provider_id", "node-1")),
            capabilities=payload.get("capabilities", ["reasoning"]),
            score=float(payload.get("score", 1.0)),
        )

    @app.post("/api/phase5/market/match")
    def phase5_market_match(payload: dict) -> dict:
        return {"matches": daemon.compute_market.match(str(payload.get("need", "reasoning")))}

    @app.post("/api/phase5/twin/update")
    def phase5_twin_update(payload: dict) -> dict:
        return daemon.digital_twin.update(
            user_id=str(payload.get("user_id", "local-user")),
            workflow_model=payload.get("workflow_model", {}),
            preferences=payload.get("preferences", {}),
        )

    @app.get("/api/phase5/status")
    def phase5_status() -> dict:
        return {
            "mesh_nodes": daemon.mesh.nodes,
            "routes": daemon.mesh.routes,
            "federated_memory": daemon.semantic_memory.records,
            "market": daemon.compute_market.providers,
            "twins": daemon.digital_twin.twins,
            "collective_patterns": daemon.collective.patterns,
        }

    return app
