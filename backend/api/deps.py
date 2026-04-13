import sys
import io
import os

from src.core.memory import MemoryManager
from src.core.brain import Brain
from src.llm.langchain_client import LangChainClient

class LogCapture(io.StringIO):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.original_stdout = sys.stdout

    def write(self, text):
        # Prevent completely blank whitespace pings
        if text.strip():
            self.logs.append(text.strip())
        self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

# Globally lock outputs securely through the active array trace dynamically!
log_capture = LogCapture()
sys.stdout = log_capture

# 1. Global Engine Initialization
print("BOOTING EXTRACTED ENGRAMTRACE KNOWLEDGE GRAPH ENGINE...")
kb_path = "src/memory/knowledge_base.html"
p_embeddings_path = "src/memory/p_embeddings.json"

print("Starting LLM Models...")
llm = LangChainClient()

print("Hydrating Matrix Indexes...")
memory = MemoryManager(kb_path=kb_path, p_embeddings_path=p_embeddings_path)

print("Synchronizing Drift Hooks...")
brain = Brain(memory_manager=memory, llm_client=llm)
