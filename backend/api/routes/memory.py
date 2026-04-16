from fastapi import APIRouter, Request
from api.deps import brain

router = APIRouter()

@router.delete("/memory")
async def clear_memory(request: Request):
    """Selectively wipes KB, stage log, and session log."""
    try:
        try:
            body = await request.json()
            wipe_kb = body.get("knowledge_base", True)
            wipe_session = body.get("session_log", True)
            wipe_stage = body.get("stage_log", True)
            wipe_trace = body.get("current_trace", True)
        except Exception:
            wipe_kb = wipe_session = wipe_stage = wipe_trace = True

        if wipe_kb:
            brain.memory.wipe()
        brain.engram_trace.wipe(wipe_stage=wipe_stage, wipe_session=wipe_session, wipe_trace=wipe_trace)
        return {"status": "success", "message": "Memory selectively wiped."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.put("/kb")
async def save_kb(request: Request):
    """Accepts raw HTML from the frontend editor, re-parses, finalizes IDs, and rebuilds embeddings."""
    from bs4 import BeautifulSoup
    body = await request.json()
    html_content = body.get("html", "")
    if not html_content.strip():
        return {"status": "error", "message": "Empty HTML content"}
    try:
        brain.memory.soup = BeautifulSoup(html_content, "lxml")
        brain.memory._finalize_and_sync(brain.llm, hierarchical=True)
        return {"status": "success", "message": "KB saved and embeddings rebuilt."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/trace/toggle")
async def toggle_trace(request: Request):
    """Toggles a selector in the active engram trace set."""
    body = await request.json()
    node_id = body.get("id", "")
    if not node_id:
        return {"status": "error", "message": "No id provided."}
    if node_id in brain.engram_trace.current_trace:
        brain.engram_trace.current_trace.discard(node_id)
        return {"status": "removed", "id": node_id, "trace": list(brain.engram_trace.current_trace)}
    else:
        brain.engram_trace.current_trace.add(node_id)
        return {"status": "added", "id": node_id, "trace": list(brain.engram_trace.current_trace)}
