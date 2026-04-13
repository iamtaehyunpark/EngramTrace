from fastapi import APIRouter, Request
from api.deps import brain

router = APIRouter()

@router.delete("/memory")
async def clear_memory():
    """Wipes the entire KB, stage log, session log, and embedding dictionary."""
    try:
        brain.memory.wipe()
        brain.engram_trace.wipe()
        return {"status": "success", "message": "Memory fully wiped."}
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
