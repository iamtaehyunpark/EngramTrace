import json
import os
import numpy as np
from datetime import datetime
from src.core.memory import MemoryManager

class EngramTrace:
    def __init__(self):
        self.current_trace = {} # retrieved selectors in this stage
        self.q_vecs = [] # query vectors in this stage
        self.stage_log_path = "src/memory/current_stage_log.json"

    def _clear_stage_log(self):
        with open(self.stage_log_path, "w") as f:
            json.dump([], f)

    def _get_stage_log(self):
        with open(self.stage_log_path, "r") as f:
            return json.load(f)
    
    def _get_last_stage_time(self):
        try:
            with open(self.stage_log_path, "r") as f:
                log = json.load(f)
                if log and isinstance(log, list):
                    return datetime.fromisoformat(log[-1]["timestamp"])
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
            pass
        return None

    def _get_stage_context(self):
        """
        Returns a structurally minimized subset of the HTML Knowledge Base.
        Efficiently strings together the outer HTML of the nearest valid parents spanning the matched IDs.
        """
        parents = set()
        for id in self.current_trace:
            tag = self.memory.soup.find(id=id) if hasattr(self, 'memory') else None
            if tag and tag.parent: 
                parents.add(tag.parent)
                
        return "\n".join([str(p) for p in parents])
    
    def _calculate_stage_drift(self, query_vec):
        """
        Detects if the user is still on the same 'Stage' (topic).
        Compares new query vector against the average vector of the current stage.
        """
        if not self.q_vecs:
            return 1.0  # No drift if the log is empty
        
        avg_vec = np.mean(self.q_vecs, axis=0)
        norm_product = np.linalg.norm(avg_vec) * np.linalg.norm(query_vec)
        if norm_product == 0: return 0
        return np.dot(avg_vec, query_vec) / norm_product

    def BufferQAPair(self, query, response):
        """
        Appends the latest interaction to the Stage Log.
        """
        log = self._get_stage_log() if os.path.exists(self.stage_log_path) else []
        log.append({
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        with open(self.stage_log_path, "w") as f:
            json.dump(log, f)

    def start_new_stage(self):
        """
        Starts a new stage by clearing the current stage log and resetting the trace.
        """
        log = self._get_stage_log() if os.path.exists(self.stage_log_path) else []
        if log:
            self._archive_stage(log)
        self._clear_stage_log()
        self.current_trace = set()
        self.q_vecs = []

    def _archive_stage(self, log):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = f"src/memory/stage_history/stage_{timestamp}.json"
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(archive_path, "w") as f:
            json.dump(log, f)


class Brain:
    def __init__(self, memory_manager: MemoryManager, llm_client, threshold=0.75):
        self.memory = memory_manager
        self.llm = llm_client
        self.threshold = threshold
        self.engram_trace = EngramTrace()
        
        # Explicit scope hook for context fetching 
        self.engram_trace.memory = memory_manager
        self.engram_trace.current_trace = set()
        
        if not os.path.exists(self.engram_trace.stage_log_path):
            os.makedirs(os.path.dirname(self.engram_trace.stage_log_path), exist_ok=True)
            self.engram_trace._clear_stage_log()
        else:
            # Phase 3: Drift Persistency. Reconstruct active vector memory from file!
            try:
                log = self.engram_trace._get_stage_log()
                active_queries = [item['query'] for item in log]
                if active_queries:
                    self.engram_trace.q_vecs = self.llm.generate_embeddings(active_queries)
            except Exception:
                pass

    def consolidate_and_transition(self):
        """
        Merges the ephemeral Stage Log natively via the LLM back into the HTML KB.
        """
        log = self.engram_trace._get_stage_log()
        if not log:
            return

        parents = set()
        for p_id in self.engram_trace.current_trace:
            tag = self.memory.soup.find(id=p_id)
            if tag and tag.parent:
                parents.add(tag.parent) 

        if len(parents) == 0:
            updated_parts = self.llm.synthesize_session(log, self.memory.soup.get_text())
        else:
            context_str = "\n".join([p.decode_contents() for p in parents])
            updated_parts = self.llm.synthesize_session(log, context_str)

        # 3. Merging with KB structurally
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(updated_parts, "lxml")
        
        for tag in soup.find_all(recursive=False):
            if tag.name in ["html", "body"]:
                for child in tag.find_all(recursive=False):
                    selector = f"{child.name}"
                    if child.get('id'): selector += f"#{child.get('id')}"
                    self.memory.rewrite(selector, str(child))
            else:
                selector = f"{tag.name}"
                if tag.get('id'): selector += f"#{tag.get('id')}"
                self.memory.rewrite(selector, str(tag))
        
        # 4. Process all physical rewrite mutations over physical index syncing
        self.memory._finalize_and_sync(self.llm)
        
        # 5. Transition log cycle
        self.engram_trace.start_new_stage()

    def run_inference(self, query: str):
        """The main cognitive loop: Drift Check -> Retrieval -> Inference -> Buffer."""
        q_vec = self.llm.generate_embeddings([query])[0]
        
        # 2. Drift Detection
        similarity = self.engram_trace._calculate_stage_drift(q_vec)
        if similarity < self.threshold:
            last_stage_time = self.engram_trace._get_last_stage_time()
            # Day logic baseline
            if last_stage_time and (datetime.now() - last_stage_time).total_seconds() > 4000:
                print("day changed")
                self.memory.atomizer(self.llm, compress=True)
                self.engram_trace.start_new_stage()
            else:
                print(f"Topic Drift Detected ({similarity:.2f}). Consolidating Stage...")
                self.consolidate_and_transition()

        self.engram_trace.q_vecs.append(q_vec)

        # 3. Ecphory
        # Safely extract hits directly from vectorized embeddings lookup
        hit_ids = self.memory.semantic_search(q_vec)
        self.engram_trace.current_trace.update(hit_ids)
        
        working_context = self.engram_trace._get_stage_context()
        stage_history = self.engram_trace._get_stage_log()
        
        # 4. Standard Response 
        response = self.llm.generate_response(
            query=query, 
            context=working_context, 
            history=stage_history
        )

        # 5. Sensory Buffering
        self.engram_trace.BufferQAPair(query, response)
        
        return response
