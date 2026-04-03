import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__))

from src.core.memory import MemoryManager
from src.core.brain import Brain

class MockLLMClient:
    def __init__(self):
        self.compress_triggered = False

    def generate_structured_html(self, raw_text: str, compress: bool = False) -> str:
        # Mock HTML generation
        if compress:
            self.compress_triggered = True
            return "<html><body><main id='root'><h1>Compressed Day</h1><p>Compressed knowledge node.</p></main></body></html>"
        return "<html><body><main id='root'><h1>New Node</h1><p>This is mock generated structural knowledge from plain text.</p></main></body></html>"

    def synthesize_session(self, log_history: list, context_html: str) -> str:
        # Generate entirely new grafted section test block
        return "<section id='graft-test'><h2>Grafted Section</h2><p id='grafted-p'>This node was grafted completely dynamically due to topic drift!</p></section>"

    def generate_embeddings(self, text: list):
        # We need distinct vectors to trigger math drift
        vectors = []
        for t in text:
            if "orthogonal" in t.lower():
                arr = np.zeros(256)
                arr[1] = 1.0
                vectors.append(arr.tolist())
            else:
                arr = np.zeros(256)
                arr[0] = 1.0
                vectors.append(arr.tolist())
        return vectors
        
    def generate_response(self, query: str, context: str, history: list) -> str:
        return "This is a strictly mock response generated from fake local context buffers."


def run_pipeline():
    print("====================================================")
    print("🚀 BOOTING ENGRAMTRACE MOCK E2E SIMULATION ENGINE 🚀")
    print("====================================================\n")
    
    # 1. SETUP
    print("[1/5] Injecting test routes natively bypassing APIs...")
    test_kb = "src/memory/test_kb.html"
    test_embed = "src/memory/test_embeddings.json"
    
    if os.path.exists(test_kb): os.remove(test_kb)
    if os.path.exists(test_embed): os.remove(test_embed)
    log_path = "src/memory/current_stage_log.json"
    if os.path.exists(log_path): os.remove(log_path) # Force fresh drift log
    
    memory = MemoryManager(kb_path=test_kb, p_embeddings_path=test_embed)
    llm = MockLLMClient()
    brain = Brain(memory_manager=memory, llm_client=llm, threshold=0.75)
    print("✅ System securely constructed.")

    # 2. INITIALIZATION
    print("\n[2/5] Triggering system initialization against an empty base...")
    # Because KB is empty, let's artificially run atomizer manually to mock the initial text drop
    memory.atomizer(llm, raw_text="System initialize first query pattern format.")
    
    # Now run an inference loop!
    # Because of memory, the first loop acts as the staging root.
    resp1 = brain.run_inference("First normal interaction")
    
    # Check what vectors were buffered:
    if len(brain.engram_trace.q_vecs) == 1:
        print("✅ Ecphory retrieval successfully routed through inference returning valid buffers.")
        
    # 3. TOPIC DRIFT & CONSOLIDATION
    print("\n[3/5] Injecting orthogonal vector query to simulate topic shift Phase Drift...")
    resp2 = brain.run_inference("completely orthogonal alien query!")
    
    # This should have triggered consolidate_and_transition printing "Topic Drift Detected" internally!
    # Let's verify Upsert grafting worked natively by checking the HTML dump!
    with open(test_kb, "r") as f:
        html_contents = f.read()
        if "graft-test" in html_contents:
            print("✅ consolidation_and_transition logically grafted brand new LLM blocks dynamically into <main>!")
        else:
            print("❌ Grafting error detected.")

    # 4. DAY SYSTEM HOMEOSTASIS
    print("\n[4/5] Hacking chronological clock natively to simulate +Day Decay Cycle...")
    
    # First, populate the new stage log with a baseline so we can actually drift away from it!
    brain.run_inference("Baseline query for day 2")
    
    # Open stage_log_path directly and override the timestamp backward natively
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            data = json.load(f)
            
        # Push all logs exactly 5000 seconds into the past
        for entry in data:
            old_time = datetime.fromisoformat(entry['timestamp'])
            new_time = old_time - timedelta(seconds=5000)
            entry['timestamp'] = new_time.isoformat()
            
        with open(log_path, "w") as f:
            json.dump(data, f)
            
        print("Clock successfully set 5000s logically into history.")
        
        # Fire inference normally. By explicitly passing 'orthogonal', we trigger the drift drop mathematically!
        # Because the logged baseline is now mathematically old, it routes through atomizer(compress=True)
        resp3 = brain.run_inference("Orthogonal time decay check!")
        
        if llm.compress_triggered:
            print("✅ Homeostatic boundary conditions successfully passed compress=True natively into the execution chain.")
        else:
            print("❌ Compress execution logic dropped!")
            
    print("\n====================================================")
    print("🏁 PIPELINE E2E SIMULATION VERIFICATION CONCLUDED 🏁")
    print("====================================================")

if __name__ == "__main__":
    run_pipeline()
