import os
import sys
import json
import pytest

# Ensure the backend directory is in the python path to resolve src imports properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.memory import MemoryManager

class MockLLMClient:
    def generate_structured_html(self, raw_text):
        return "<html><body><main id='root'><section id='sec-1'><p id='p-1'>Text 1</p><p id='p-2'>Text 2</p></section></main></body></html>"

    def generate_embeddings(self, texts):
        return [[0.1, 0.2] for _ in texts]

@pytest.fixture
def mem_and_llm():
    """
    Setup isolated test scope files and teardown safely.
    """
    test_kb = "src/memory/test_kb.html"
    test_embed = "src/memory/test_p_embeddings.json"
    
    if os.path.exists(test_kb): os.remove(test_kb)
    if os.path.exists(test_embed): os.remove(test_embed)
    
    mem = MemoryManager(kb_path=test_kb, p_embeddings_path=test_embed)
    llm = MockLLMClient()
    
    yield mem, llm, test_kb, test_embed
    
    # Teardown scope
    if os.path.exists(test_kb): os.remove(test_kb)
    if os.path.exists(test_embed): os.remove(test_embed)

# 1. Test Atomization and DOM state initialization
def test_atomizer_generates_ids(mem_and_llm):
    mem, llm, _, _ = mem_and_llm
    text = "Artificial intelligence relies on robust memory systems."
    
    ids = mem.atomizer(text, llm)
    
    assert ids == ['p-1', 'p-2']
    assert mem.soup is not None
    assert mem.soup.find(id='p-1') is not None

# 2. Test Vector Processing & Syncing to Map JSON
def test_update_adds_new_embeddings(mem_and_llm):
    mem, llm, _, test_embed = mem_and_llm
    ids = mem.atomizer("Test string", llm)
    
    mem.update_p_embeddings(llm, ids)
    assert os.path.exists(test_embed)
    
    with open(test_embed, "r") as f:
        data = json.load(f)
        assert 'p-1' in data
        assert 'p-2' in data
        assert data['p-1']['selector'] == 'html > body > main#root > section#sec-1 > p#p-1'
        assert len(data['p-1']['vector']) == 2

# 3. Test Object Mapping Schema Exact Syntax
def test_verify_json_schema(mem_and_llm):
    mem, llm, _, test_embed = mem_and_llm
    ids = mem.atomizer("Test schema", llm)
    mem.update_p_embeddings(llm, ids)
    
    with open(test_embed, "r") as f:
        data = json.load(f)
        assert 'selector' in data['p-1']
        assert 'vector' in data['p-1']
        assert 'last_consolidated' in data['p-1']

# 4. Test ID properties prune & wipe safely
def test_deletion_and_pruning(mem_and_llm):
    mem, llm, _, test_embed = mem_and_llm
    ids = mem.atomizer("Test prune", llm)
    mem.update_p_embeddings(llm, ids)
    
    # 1. Simulate HTML node physical deletion in front-end
    mem.soup.find(id='p-1').decompose()
    mem.save_kb(mem.soup.prettify())
    
    # 2. Run sequential sync (the active target is only p-2)
    mem.update_p_embeddings(llm, ['p-2'])
    
    with open(test_embed, "r") as f:
        data = json.load(f)
        assert 'p-1' not in data  # Safely pruned because it detached from tree
        assert 'p-2' in data      # Remained mapped
