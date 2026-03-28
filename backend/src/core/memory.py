"""
1. Physical Memory Orchestration (memory.py)
This layer handles the "Body" of the system—the raw data and its spatial organization.

AtomizeContext(text): Splits raw input into granular strings and wraps them 
    into a strictly formatted HTML structure with unique IDs (p#p-1, etc.).

GeneratePEmbeddings(html_selectors): Iterates through all <p> tags, extracts their full content, 
    and calls the LLM to generate vectors.

UpdateKBNode(selector_id, new_content): Specifically targets an HTML element by ID and replaces its inner text 
    without breaking the document structure.

CommitPhysicalMemory(): Synchronizes the in-memory BeautifulSoup object to knowledge_base.html and the vector list to p_embeddings.json.
"""

import os
import json
from bs4 import BeautifulSoup
import uuid
import hashlib

class MemoryManager:
    def __init__(self, kb_path="src/memory/knowledge_base.html", p_embeddings_path="src/memory/p_embeddings.json"):
        self.kb_path = kb_path
        self.p_embeddings_path = p_embeddings_path
        self.soup = self._load_or_create_kb()

# INITILIZE KNOWLEDGE BASE
    # initialize knowledge base
    def _load_or_create_kb(self):
        """Loads the KB if it exists, otherwise initializes a root skeleton."""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "lxml")
        return BeautifulSoup("<html><body><main id='root'></main></body></html>", "lxml")

    # atomize context
    def atomizer(self, raw_text, llm_client):
        """
        Uses the LLM to semantically structure raw text into HTML.
        """        
        # Call your LangChain/Gemini client
        generated_html = llm_client.generate_structured_html(raw_text)

        # Finalize atomization
        finalized_html = self.finalize_atomization(generated_html)
        
        # Update class state with the new HTML string
        self.soup = BeautifulSoup(finalized_html, "lxml")

        # Validate and save
        self.save_kb(finalized_html)
        
        return [p['id'] for p in self.soup.find_all('p')] # return list of p tags

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
    
    # update p embeddings
    def update_p_embeddings(self, llm_client, ids):
        """
        Updates p embeddings for given ids.
        pseudo code:
        delete p_embeddings for given ids
        add p_embeddings for given ids
        delete_unused_p_embeddings()
        """
        self.delete_p_embeddings(ids)
        self.add_p_embeddings(llm_client, ids)
        self.delete_unused_p_embeddings()

    # add p embeddings for given ids
    def add_p_embeddings(self, llm_client, ids):
        """
        Iterates through the HTML, finds text for each <p>, 
        generates vectors, and saves to p_embeddings.json.
        """
        from datetime import datetime

        embedding_map = {}
        if os.path.exists(self.p_embeddings_path):
            with open(self.p_embeddings_path, "r") as f:
                try:
                    embedding_map = json.load(f)
                except json.JSONDecodeError:
                    pass

        valid_ids = []
        contents = []
        selectors = []

        for p_id in ids:
            tag = self.soup.find(id=p_id)
            if tag:
                valid_ids.append(p_id)
                contents.append(tag.get_text())

                # selector that matches id in kb_path
                parents = list(tag.parents)
                path_parts = []
                for p in reversed(parents):
                    if p.name and p.name != '[document]':
                        if p.get('id'):
                            path_parts.append(f"{p.name}#{p.get('id')}")
                        else:
                            path_parts.append(p.name)
                path_parts.append(f"p#{p_id}")
                selectors.append(" > ".join(path_parts))

        if valid_ids:
            # Batch generate vectors for efficiency
            vectors = llm_client.generate_embeddings(contents)

            for i, p_id in enumerate(valid_ids):
                embedding_map[p_id] = {
                    "selector": selectors[i],
                    "vector": vectors[i],
                    "last_consolidated": datetime.now().isoformat()
                }

            os.makedirs(os.path.dirname(self.p_embeddings_path), exist_ok=True)
            with open(self.p_embeddings_path, "w") as f:
                json.dump(embedding_map, f, indent=4)

    # Delete p embeddings for given ids
    def delete_p_embeddings(self, ids):
        """
        Deletes p embeddings for given ids.
        pseudo code:
        for(id in ids):
            if(id is included in the p_embedding_path.json file):
                delete the id from the p_embedding_path.json file
        """
        if not os.path.exists(self.p_embeddings_path):
            return

        with open(self.p_embeddings_path, "r") as f:
            try:
                embedding_map = json.load(f)
            except json.JSONDecodeError:
                return

        for p_id in ids:
            if p_id in embedding_map:
                del embedding_map[p_id]

        with open(self.p_embeddings_path, "w") as f:
            json.dump(embedding_map, f, indent=4)    
            
    def delete_unused_p_embeddings(self):
        """
        Delete p_embeddings that are not used in the knowledge base.
        """
        existing_p_tags = self.soup.find_all('p')
        existing_ids = [p['id'] for p in existing_p_tags]

        with open(self.p_embeddings_path, "r") as f:
            embedding_map = json.load(f)

        if not isinstance(embedding_map, dict):
            print("Warning: p_embeddings.json is not a dictionary. Skipping deletion.")
            return

        keys_to_delete = [k for k in embedding_map.keys() if k not in existing_ids]

        for key in keys_to_delete:
            del embedding_map[key]

        with open(self.p_embeddings_path, "w") as f:
            json.dump(embedding_map, f, indent=4)
        
        print(f"Deleted {len(keys_to_delete)} unused embeddings.")



"""
2. The Ecphory Engine (ecphory.py or memory.py)
This handles the "Retrieval" logic—turning a query into a focused "Working Page."

SemanticSearch(query_vector): Performs a cosine similarity check against the p_embeddings.json 
    and returns a list of "hit" selector IDs.

ExtractSelectorPath(target_id): Backtracks from a specific ID to the root (e.g., html > body > section > p#p-42) 
    to ensure hierarchical context.

AssembleEngramTrace(hit_ids): A "Pruning" function that creates a temporary HTML file (The Working Page) 
    containing only the activated nodes and their parent summaries.

DeReferenceTrace(): Converts the HTML Working Page into a clean Markdown/Text format for the LLM to read during inference.
"""

import numpy as np
import json

def semantic_search(self, query_vector, threshold=0.7, top_n=5):
    """
    Compares query vector against all P-embeddings.
    Returns: List of hit IDs that pass the threshold.
    """
    if not os.path.exists(self.embedding_path):
        return []

    with open(self.embedding_path, "r") as f:
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
    
    # Sort by highest similarity
    hits.sort(key=lambda x: x[1], reverse=True)
    
    return [hit[0] for hit in hits[:top_n]]