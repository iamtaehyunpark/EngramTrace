"""
1. Physical Memory Orchestration (memory.py)
This layer handles the "Body" of the system—the raw data and its spatial organization.
"""

import numpy as np
import json
import os
from bs4 import BeautifulSoup
import uuid
import hashlib
from src.llm.langchain_client import LangChainClient

class MemoryManager:
    def __init__(self, kb_path="src/memory/knowledge_base.html", p_embeddings_path="src/memory/p_embeddings.json", working_page_path="src/memory/working_page.txt"):
        self.kb_path = kb_path
        self.p_embeddings_path = p_embeddings_path
        self.working_page_path = working_page_path
        self.soup = self._load_or_create_kb()

# INITILIZE KNOWLEDGE BASE
    # initialize knowledge base
    def _load_or_create_kb(self):
        """Loads the KB if it exists, otherwise initializes a root skeleton."""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "lxml")
        return BeautifulSoup("<html><body><main id='root'></main></body></html>", "lxml")

    def atomizer(self, llm_client, raw_text=None, compress=False):
        """
        Uses the LLM to semantically structure raw text into HTML.
        If raw_text is None, it globally regenerates the KB (compressing it strictly if a Day Phase triggered!).
        """        
        if raw_text is None:
            # Re-read existing HTML back into a dense string
            kb_text = self.soup.get_text(separator='\n', strip=True)
            generated_html = llm_client.generate_structured_html(kb_text, compress=compress)
        else:
            generated_html = llm_client.generate_structured_html(raw_text, compress=compress)

        # Drop the AI generation cleanly into active memory wrapper natively 
        self.soup = BeautifulSoup(generated_html, "lxml")
        
        # Divert to the central node tracker securing validation loops inherently
        return self._finalize_and_sync(llm_client)

    def _finalize_and_sync(self, llm_client):
        """
        Synchronizes manual structural DOM edits backward onto the physical KB.
        Assigns hashes to unknown/raw nodes and triggers vector rebuilding loops securely!
        """
        finalized_html = self.finalize_atomization(str(self.soup))
        self.soup = BeautifulSoup(finalized_html, "lxml")
        self.save_kb(finalized_html)

        all_p_tags = [p['id'] for p in self.soup.find_all('p')]
        self.sync_embeddings(llm_client, all_p_tags)
        return all_p_tags

    def rewrite(self, selector: str, updated_content: str):
        """
        Safely swaps interior content of an existing node, or splices new blocks globally.
        Matches node via CSS selector path (e.g. 'html > body > p#p-123').
        """
        target = self.soup.select_one(selector)
        if target:
            target.clear()
            target.append(BeautifulSoup(updated_content, "html.parser"))
            return True
            
        # Upsert grafting: If this is a structural element entirely new to the graph, 
        # seamlessly attach it to the primary graph tree root natively!
        root_container = self.soup.find(id="root") or self.soup.find("body")
        if root_container:
            root_container.append(BeautifulSoup(updated_content, "html.parser"))
            return True
            
        return False


    def _generate_deterministic_id(self, text: str) -> str:
        """
        Generates a stable ID based on the text content.
        If the text is the same, the ID will always be the same.
        """
        # Create a SHA-256 hash of the text
        hash_digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        # Use the first 12 characters for a clean 'p-XXXX' ID
        return f"p-{hash_digest[:12]}"

    def finalize_atomization(self, generated_html: str):
        """
        Processes the AI's HTML, ensuring every <p> has a stable, manual ID.
        """
        soup = BeautifulSoup(generated_html, "lxml")
        
        # Find all <p> tags that don't have an 'id' attribute
        for p_tag in soup.find_all('p', id=False):
            # Generate ID from the content itself
            stable_id = self._generate_deterministic_id(p_tag.get_text())
            p_tag['id'] = stable_id
            
        return soup.prettify()

    def save_kb(self, content):
        """Persists the BeautifulSoup object to the HTML file."""
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, "w", encoding="utf-8") as f:
            f.write(content)



    # get all p contents
    def get_all_p_contents(self):
        """Returns a map of {selector_id: text_content} for all p tags."""
        return {p['id']: p.get_text() for p in self.soup.find_all('p')}
    
    def sync_embeddings(self, llm_client, active_ids):
        """
        Calculates difference matrices sequentially natively.
        Extracts new vectors, sweeps obsolete arrays natively, and pushes memory explicitly once via single active dump limit.
        """
        from datetime import datetime
        
        # 1. Load active embedding JSON state fully mapped memory strictly ONE TIME
        embedding_map = {}
        if os.path.exists(self.p_embeddings_path):
            with open(self.p_embeddings_path, "r") as f:
                try:
                    embedding_map = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        # 2. Prune globally dead selectors missing mapped keys
        if isinstance(embedding_map, dict):
            dead_nodes = [k for k in embedding_map.keys() if k not in active_ids]
            for key in dead_nodes:
                del embedding_map[key]

        # 3. Formulate physical string payloads array map bypassing unchanged roots 
        new_nodes = []
        new_contents = []
        new_selectors = []
        
        for p_id in active_ids:
            if p_id not in embedding_map:
                tag = self.soup.find(id=p_id)
                if tag:
                    new_nodes.append(p_id)
                    new_contents.append(tag.get_text())
                    
                    parents = list(tag.parents)
                    path_parts = []
                    for p in reversed(parents):
                        if p.name and p.name != '[document]':
                            if p.get('id'):
                                path_parts.append(f"{p.name}#{p.get('id')}")
                            else:
                                path_parts.append(p.name)
                    path_parts.append(f"p#{p_id}")
                    new_selectors.append(" > ".join(path_parts))
        
        # 4. Synthesize vectors sequentially natively 
        if new_nodes:
            vectors = llm_client.generate_embeddings(new_contents)
            for i, p_id in enumerate(new_nodes):
                embedding_map[p_id] = {
                    "selector": new_selectors[i],
                    "vector": min(vectors[i], vectors[i]) if hasattr(vectors[i], '__iter__') else vectors[i], # Just safety fallback
                    "last_consolidated": datetime.now().isoformat()
                }
                embedding_map[p_id]["vector"] = vectors[i] # Set properly 
        
        # 5. Flush and persist mapped JSON precisely locally ONE time
        os.makedirs(os.path.dirname(self.p_embeddings_path), exist_ok=True)
        with open(self.p_embeddings_path, "w") as f:
            json.dump(embedding_map, f, indent=4)

    def semantic_search(self, query_vector, threshold=0.7):
        """
        Compares query vector against all P-embeddings.
        Returns: List of hit IDs that pass the threshold.
        """
        if not os.path.exists(self.p_embeddings_path):
            return []

        with open(self.p_embeddings_path, "r") as f:
            embedding_map = json.load(f)

        if not embedding_map:
            return []

        # 1. Prepare data for NumPy
        ids = list(embedding_map.keys())
        # Convert list of vectors to a 2D NumPy array
        vectors = np.array([item['vector'] for item in embedding_map.values()], dtype='float32')
        q_vec = np.array(query_vector, dtype='float32')

        # 2. Vectorized Cosine Similarity Math
        # similarity = (A . B) / (||A|| * ||B||)
        dot_product = np.dot(vectors, q_vec)
        norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(q_vec)
        
        # Avoid div/0 error by applying a small epsilon
        norms = np.where(norms == 0, 1e-10, norms)
        similarities = dot_product / norms

        # 3. Filter by threshold and sort
        hits = []
        for i, score in enumerate(similarities):
            if score >= threshold:
                hits.append((ids[i], score))
        
        return [hit[0] for hit in hits]
