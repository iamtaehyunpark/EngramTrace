import os
import json
from src.core.memory import MemoryManager
from src.core.brain import Brain
from src.llm.langchain_client import LangChainClient

def load_env():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k] = v.strip("'").strip('"')

def run_tests():
    load_env()
    test_kb = "tmp_test/knowledge_base.html"
    test_emb = "tmp_test/p_embeddings.json"
    
    os.makedirs("tmp_test", exist_ok=True)
    
    # 1. Setup Initial Mock KB
    initial_kb = '<html><body><main id="root">\n  <section id="sec-1">\n    <p id="p-1">Original facts about cats.</p>\n  </section>\n</main></body></html>'
    with open(test_kb, "w") as f:
        f.write(initial_kb)
        
    print("=== INITIAL KNOWLEDGE BASE ===")
    print(initial_kb)
    
    # Initialize System Core
    llm = LangChainClient()
    memory = MemoryManager(kb_path=test_kb, p_embeddings_path=test_emb)
    # The brain instantiates an EngramTrace which creates parent dirs for its log path.
    brain = Brain(memory_manager=memory, llm_client=llm)
    
    # --- TEST 1: Modifying Existing Section ---
    print("\n\n" + "="*50)
    print("TEST 1: CONSOLIDATING EXISTING TRACE PARENT")
    print("Simulating a Q&A about cats, attached to p-1 (which forces sec-1 to be passed in)")
    
    # Force the trace to pull 'sec-1'
    brain.engram_trace.current_trace = {"p-1"}
    
    # Mock the log file
    brain.engram_trace.stage_log_path = "tmp_test/log1.json"
    log1 = [{"query": "What do cats look like?", "response": "Cats are extremely fluffy felines.", "timestamp": "2026-04-05"}]
    with open("tmp_test/log1.json", "w") as f:
        json.dump(log1, f)
        
    # Execute!
    brain.consolidate_and_transition()
    
    with open(test_kb, "r") as f:
        print("\n>>> RESULTING KNOWLEDGE BASE (Should show rewritten sec-1 inside Root) <<<")
        print(f.read())
        

    # --- TEST 2: Appending New Knowledge ---
    print("\n\n" + "="*50)
    print("TEST 2: CONSOLIDATING UNRELATED KNOWLEDGE")
    print("Simulating a Q&A about Dogs. No trace overlaps, so it should scrape the full KB and graft a NEW node.")
    
    # Clear trace, simulating topic drift with NO matches to the old knowledge
    brain.engram_trace.current_trace = set()
    
    brain.engram_trace.stage_log_path = "tmp_test/log2.json"
    log2 = [{"query": "What about Dogs?", "response": "Dogs are fiercely loyal and come in many breeds.", "timestamp": "2026-04-05"}]
    with open("tmp_test/log2.json", "w") as f:
        json.dump(log2, f)
        
    # Execute!
    brain.consolidate_and_transition()
    
    with open(test_kb, "r") as f:
        print("\n>>> FINAL KNOWLEDGE BASE (Should show new node seamlessly appended!) <<<")
        print(f.read())


if __name__ == "__main__":
    run_tests()
