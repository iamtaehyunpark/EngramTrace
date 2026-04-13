import json
import os
import numpy as np
from datetime import datetime
import time
import threading
from functools import wraps

def trace_timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Notice: Function '{func.__name__}' started")
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.time()
            total_duration = end_time - start_time
            print(f"Notice: Function '{func.__name__}' finished. Total time: {total_duration:.4f} seconds.")
    return wrapper
from src.core.memory import MemoryManager





class EngramTrace:
    @trace_timing
    def __init__(self):
        self.current_trace = set() # retrieved selectors in this stage
        self.qa_vecs = [] # qa vectors in this stage
        self.stage_log_path = "src/memory/current_stage_log.json"
        self.session_log_path = "src/memory/session_log.json"

    def wipe(self):
        self.current_trace = set()
        self.qa_vecs = []
        
        # Unconditionally write empty arrays so UI never hangs waiting for boot files
        os.makedirs(os.path.dirname(self.stage_log_path), exist_ok=True)
        with open(self.stage_log_path, "w") as f:
            json.dump([], f)
            
        with open(self.session_log_path, "w") as f:
            json.dump([], f)
            
        # Completely purge archived historical drift stage files
        history_dir = "src/memory/stage_history"
        if os.path.exists(history_dir):
            for file in os.listdir(history_dir):
                if file.endswith(".json"):
                    os.remove(os.path.join(history_dir, file))
                    
    def _clear_stage_log(self):
        with open(self.stage_log_path, "w") as f:
            json.dump([], f)

    def _get_stage_log(self):
        try:
            if not os.path.exists(self.stage_log_path):
                return []
            with open(self.stage_log_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
            
    def _get_session_log(self):
        try:
            if not os.path.exists(self.session_log_path):
                return []
            with open(self.session_log_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _get_last_stage_time(self, log=None):
        try:
            if log is None:
                with open(self.stage_log_path, "r") as f:
                    log = json.load(f)
            if log and isinstance(log, list):
                return datetime.fromisoformat(log[-1]["timestamp"])
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
            pass
        return None

    @trace_timing
    def _get_stage_context(self):
        """
        Returns a structurally minimized subset of the HTML Knowledge Base.
        Efficiently strings together the outer HTML of the nearest valid parents spanning the matched IDs.
        """
        print("[EngramTrace] Abstracting parent-node vectors synthesizing structural Ecphory...")
        parents = set()
        for id in self.current_trace:
            tag = self.memory.soup.find(id=id) if hasattr(self, 'memory') else None
            if tag and tag.parent: 
                parents.add(tag.parent)
                
        return "\n".join([str(p) for p in parents])
    
    @trace_timing
    def _calculate_stage_drift(self, query_vec):
        """
        Detects if the user is still on the same 'Stage' (topic).
        Compares new query vector against the average vector of the current stage.
        """
        if len(self.qa_vecs) < 1:
            session_log = self._get_session_log()
            if session_log and "last_qa_vec" in session_log[-1]:
                avg_vec = np.array(session_log[-1]["last_qa_vec"])
            else:
                return 0.0  # Drift if the log is empty --> handled by run_inference()
        else:
            avg_vec = np.mean(self.qa_vecs, axis=0) 
            
        norm_product = np.linalg.norm(avg_vec) * np.linalg.norm(query_vec)
        if norm_product == 0: return 0
        return np.dot(avg_vec, query_vec) / norm_product

    @trace_timing
    def BufferQAPair(self, query, response, qa_vec=None):
        """
        Appends the latest interaction to the Stage Log and permanent Session Log.
        """
        qa_block = {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Ephemeral Stage Log (Wiped on drift)
        stage = self._get_stage_log()
        stage.append(qa_block)
        with open(self.stage_log_path, "w") as f:
            json.dump(stage, f)
            
        # 2. Permanent Session Log (Continual History)
        session_qa_block = dict(qa_block)
        if qa_vec is not None:
            session_qa_block["last_qa_vec"] = qa_vec if isinstance(qa_vec, list) else getattr(qa_vec, "tolist", lambda: qa_vec)()
            
        session = self._get_session_log()
        if session and "last_qa_vec" in session[-1]:
            del session[-1]["last_qa_vec"]
            
        session.append(session_qa_block)
        with open(self.session_log_path, "w") as f:
            json.dump(session, f)

    @trace_timing
    def start_new_stage(self):
        """
        Starts a new stage by clearing the current stage log and resetting the trace.
        """
        log = self._get_stage_log() if os.path.exists(self.stage_log_path) else []
        if log:
            self._archive_stage(log)
        self._clear_stage_log()
        self.current_trace = set()
        self.qa_vecs = []

    @trace_timing
    def _archive_stage(self, log):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = f"src/memory/stage_history/stage_{timestamp}.json"
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        with open(archive_path, "w") as f:
            json.dump(log, f)






class Brain:
    @trace_timing
    def __init__(self, memory_manager: MemoryManager, llm_client, stage_threshold=0.83, search_threshold=0.80):
        self.memory = memory_manager
        self.llm = llm_client
        self.stage_threshold = stage_threshold
        self.search_threshold = search_threshold
        self.engram_trace = EngramTrace()
        
        # Explicit scope hook for context fetching 
        self.engram_trace.memory = memory_manager
        self.engram_trace.current_trace = set()
        
        if not os.path.exists(self.engram_trace.stage_log_path):
            os.makedirs(os.path.dirname(self.engram_trace.stage_log_path), exist_ok=True)
            self.engram_trace._clear_stage_log()
            
        if not os.path.exists(self.engram_trace.session_log_path):
            os.makedirs(os.path.dirname(self.engram_trace.session_log_path), exist_ok=True)
            with open(self.engram_trace.session_log_path, "w") as f:
                json.dump([], f)
        else:
            # Phase 3: Drift Persistency. Reconstruct active vector memory from file!
            try:
                log = self.engram_trace._get_stage_log()
                active_qa = [f"Q: {item['query']}\nA: {item['response']}" for item in log[-3:]]
                if active_qa:
                    self.engram_trace.qa_vecs = self.llm.generate_embeddings(active_qa)
            except Exception:
                pass

    @trace_timing
    def consolidate_and_transition(self):
        """
        Merges the ephemeral Stage Log natively via the LLM back into the HTML KB.
        """
        print("[Brain.consolidate_and_transition] Merging Stage Log arrays into HTML Knowledge Base...")
        log = self.engram_trace._get_stage_log()
        if not log:
            return

        parents = set()
        for p_id in self.engram_trace.current_trace:
            tag = self.memory.soup.find(id=p_id)
            if not tag:
                continue
            if tag.parent:
                parents.add(tag.parent)
            else:
                parents.add(tag)
        
        if len(parents) == 0:
            updated_parts = self.llm.synthesize_session(log, self.memory.soup.get_text())
        else:
            context_str = "\n".join([str(p) for p in parents])
            updated_parts = self.llm.synthesize_session(log, context_str)

        # 3. Merging with KB structurally
        print("[Brain.consolidate_and_transition] Executing DOM mutations safely parsing new nodes...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(updated_parts, "lxml")
        
        # lxml parser automatically wraps in html/body. Find the actual content entries natively.
        container = soup.find('body') if soup.find('body') else soup
        
        for tag in container.find_all(recursive=False):
            if tag.name:
                # PROTECT ROOT: If the LLM wraps the response in the global 'main#root' container,
                # unwrap it and iterate over its children to prevent replacing the entire Knowledge Base WIKI!
                if tag.name == 'main' and tag.get('id') == 'root':
                    for sub_tag in tag.find_all(recursive=False):
                        if sub_tag.name:
                            if sub_tag.get('id'):
                                self.memory.rewrite(f"{sub_tag.name}#{sub_tag.get('id')}", str(sub_tag))
                            else:
                                self.memory.rewrite(None, str(sub_tag))
                    continue
                    
                if tag.get('id'):
                    selector = f"{tag.name}#{tag.get('id')}"
                    self.memory.rewrite(selector, str(tag))
                else:
                    # If there's no ID bound to the highest tag organically, pass None to force safe graft upserts 
                    self.memory.rewrite(None, str(tag))
        
        # 4. Process all physical rewrite mutations over physical index syncing
        self.memory._finalize_and_sync(self.llm)
        
        # 5. Transition log cycle
        self.engram_trace.start_new_stage()

    @trace_timing
    def run_inference(self, query: str, stage_threshold: float = None, search_threshold: float = None, no_search: bool = False):
        """The main cognitive loop: Drift Check -> Retrieval -> Inference -> Buffer."""
        print(f"\n[Brain.run_inference] Firing Cognitive Loop on: '{query[:20]}...'")
        q_vec = self.llm.generate_embeddings([query])[0]
        
        # Resolve threshold natively allowing external parameter overrides without breaking Python scopes
        active_stage_threshold = stage_threshold if stage_threshold is not None else self.stage_threshold
        active_search_threshold = search_threshold if search_threshold is not None else self.search_threshold
        
        # Force Consolidation if certain amount of q-a pairs have been processed
        stage_log = self.engram_trace._get_stage_log()
        session_log = self.engram_trace._get_session_log()

        if len(stage_log) >= 10:
            print("Q-A pairs >= 10. Consolidating Stage...")
            self.consolidate_and_transition()
        elif len(stage_log) == 0 and not (session_log and "last_qa_vec" in session_log[-1]):
            print("Stage log empty and no prior session history. Skip drift check")
        else:
            # 2. Drift Detection
            print("[EngramTrace] Tracking stage deviation bounds (Drift Check)...")
            similarity = self.engram_trace._calculate_stage_drift(q_vec)
            print("similarity", similarity)
            if similarity < active_stage_threshold:
                last_stage_time = self.engram_trace._get_last_stage_time(log=stage_log)
                # Day logic baseline
                if last_stage_time and (datetime.now() - last_stage_time).total_seconds() > 4000:
                    print("day changed")
                    if len(stage_log) > 0:
                        self.consolidate_and_transition()
                    self.memory.atomizer(self.llm, compress=True)
                else:
                    print(f"Topic Drift Detected ({similarity:.2f}). Consolidating Stage...")
                    self.consolidate_and_transition()


        # 3. Ecphory
        # Safely extract hits directly from vectorized embeddings lookup
        if not no_search:
            hit_ids = self.memory.semantic_search(q_vec, threshold=active_search_threshold)
            self.engram_trace.current_trace.update(hit_ids)
        
        working_context = self.engram_trace._get_stage_context()
        stage_history = self.engram_trace._get_stage_log()  # Re-read: consolidation may have cleared it
        session_history = session_log[-5:]  # Reuse from earlier read
        
        # 4. Standard Response 
        response = self.llm.generate_response(
            query=query, 
            context=working_context, 
            history=stage_history,
            session_history=session_history
        )

        # 5. Semantic Generation of qa-pair and Buffering
        qa_text = f"Q: {query}\nA: {response}"
        qa_vec = self.llm.generate_embeddings([qa_text])[0]
        
        self.engram_trace.qa_vecs.append(qa_vec)
        if len(self.engram_trace.qa_vecs) > 3:
            self.engram_trace.qa_vecs.pop(0)

        self.engram_trace.BufferQAPair(query, response, qa_vec=qa_vec)
        
        return response
