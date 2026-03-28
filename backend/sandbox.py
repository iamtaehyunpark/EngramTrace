import os
import sys
import json

# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    key, val = line.strip().split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")
                except ValueError:
                    continue

sys.path.append(os.path.dirname(__file__))

from src.core.memory import MemoryManager
from src.llm.langchain_client import LangChainClient

def run_part_1():
    print("================== PART 1: ATOMIZER ==================")
    print("Initializing real LangChainClient with Gemini API...")
    llm = LangChainClient()

    # We will use the standard paths now so you can see it in your IDE
    kb_path = "src/memory/knowledge_base.html"
    embed_path = "src/memory/p_embeddings.json"
    
    # Clean previous if exists just to be fresh
    if os.path.exists(kb_path): os.remove(kb_path)
    if os.path.exists(embed_path): os.remove(embed_path)

    mem = MemoryManager(kb_path=kb_path, p_embeddings_path=embed_path)

    raw_text = (
        "Project EngramFlow is an experimental non-parametric memory engine. "
        "It stores knowledge in a discrete, HTML-formatted structural format instead of relying on "
        "model weights. The engine parses new information into simple `<p>` tags with unique IDs, "
        "and embeds them sequentially so the Ecphory engine can retrieve context rapidly."
    )
    
    print("\nSending raw text to Gemini to generate structural `<p>` tag nodes...\n")
    print(f"RAW TEXT:\n{raw_text}\n")
    
    try:
        # Part 1 execution
        ids = mem.atomizer(raw_text, llm)
        
        print("✅ SUCCESS!")
        print(f"Generated IDs: {ids}")
        print(f"\nSaved structurally parsed DOM to: {os.path.abspath(kb_path)}")
        
        # Print resulting HTML to terminal so user can see what Gemini did
        with open(kb_path, "r", encoding="utf-8") as f:
            print("\n----- KNOWLEDGE BASE HTML (knowledge_base.html) -----")
            print(f.read())
            print("-----------------------------------------------------")
            
        # Part 2 execution
        print("\n================== PART 2: VECTOR EMBEDDING ==================")
        print("Batch-sending `<p>` tags to Gemini Embedding API...")
        
        mem.update_p_embeddings(llm, ids)
        print("✅ SUCCESS!")
        print(f"Saved generated vectors successfully to: {os.path.abspath(embed_path)}")
        
        with open(embed_path, "r", encoding="utf-8") as f:
            print("\n----- P EMBEDDINGS JSON (p_embeddings.json) -----")
            # We just print the keys and shapes so we don't dump hundreds of floats
            data = json.load(f)
            for k, v in data.items():
                print(f"ID: {k}")
                print(f"  └ Selector: {v['selector']}")
                print(f"  └ Timestamp: {v['last_consolidated']}")
                print(f"  └ Vector length: {len(v['vector'])}")
            print("-----------------------------------------------------")
            
        # Part 3 execution
        print("\n================== PART 3: ORPHAN NODE PRUNING ==================")
        print("Simulating HTML node removal...")
        first_id = ids[0]
        target_node = mem.soup.find(id=first_id)
        if target_node:
            target_node.decompose()
            mem.save_kb(mem.soup.prettify())
            print(f"Successfully detached <p id='{first_id}'> from knowledge_base.html")
        
        print(f"Running sequential `update_p_embeddings` on the remaining ID...")
        remaining_ids = ids[1:]
        mem.update_p_embeddings(llm, remaining_ids)
        
        with open(embed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print("\n----- FINAL P EMBEDDINGS JSON -----")
            print(f"Remaining keys successfully synced: {list(data.keys())}")
            print(f"Total entries securely retained: {len(data)}")
            print("-----------------------------------------------------")
            
        # Part 4 execution
        print("\n================== PART 4: CONTENT REFRESH / UPDATE ==================")
        print("Modifying the text of an existing node and regenerating vectors to prove sync refresh...")
        
        remaining_id = remaining_ids[0]
        node = mem.soup.find(id=remaining_id)
        
        # Modify the HTML node's string natively
        if node:
            node.string = "This content has been artificially updated to trigger a vector regeneration process."
            mem.save_kb(mem.soup.prettify())
            
        print(f"Content of <p id='{remaining_id}'> altered. Syncing vector map...")
        
        # Capture old timestamp & run update
        old_timestamp = data[remaining_id]['last_consolidated']
        mem.update_p_embeddings(llm, [remaining_id])
        
        with open(embed_path, "r", encoding="utf-8") as f:
            final_data = json.load(f)
            new_timestamp = final_data[remaining_id]['last_consolidated']
            
            print("\n----- REFRESH VALIDATION -----")
            print(f"Old ID Vector Timestamp: {old_timestamp}")
            print(f"New ID Vector Timestamp: {new_timestamp}")
            
            if new_timestamp > old_timestamp:
                print("✅ Vector entry successfully refreshed & overwritten with updated embedding properties!")
            print("-----------------------------------------------------")

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")

if __name__ == "__main__":
    run_part_1()
