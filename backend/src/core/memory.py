"""
1. Physical Memory Orchestration (memory.py)
This layer handles the "Body" of the system—the raw data and its spatial organization.

cd /Users/a/GitHub/EngramTrace/backend && source tmp_venv/bin/activate && python main.py
"""

import numpy as np
import json
import os
from bs4 import BeautifulSoup
import hashlib
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

class MemoryManager:
    STRUCTURAL_TAGS = {'body', 'main', 'section', 'article', 'div'}

    @trace_timing
    def __init__(self, kb_path="src/memory/knowledge_base.html", p_embeddings_path="src/memory/p_embeddings.json", structural_embeddings_path="src/memory/structural_embeddings.json"):
        self.kb_path = kb_path
        self.p_embeddings_path = p_embeddings_path
        self.structural_embeddings_path = structural_embeddings_path
        self.soup = self._load_or_create_kb()

    @trace_timing
    def wipe(self):
        """Wipes the physical HTML Graph and Embeddings JSON."""
        if os.path.exists(self.kb_path):
            os.remove(self.kb_path)
        if os.path.exists(self.p_embeddings_path):
            os.remove(self.p_embeddings_path)
        if os.path.exists(self.structural_embeddings_path):
            os.remove(self.structural_embeddings_path)
            
        # Reinitialize skeleton
        self.soup = self._load_or_create_kb()

# INITILIZE KNOWLEDGE BASE
    # initialize knowledge base
    @trace_timing
    def _load_or_create_kb(self):
        """Loads the KB if it exists, otherwise initializes a root skeleton."""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return BeautifulSoup(f, "lxml")
                
        # If it doesn't exist, create it physically right now
        default_html = "<html><body><main id='root'></main></body></html>"
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, "w", encoding="utf-8") as f:
            f.write(default_html)
            
        return BeautifulSoup(default_html, "lxml")

    @trace_timing
    def atomizer(self, llm_client, raw_text=None, compress=False):
        """
        Uses the LLM to semantically structure raw text into HTML.
        If raw_text is None, it globally regenerates the KB (compressing it strictly if a Day Phase triggered!).
        """        
        if raw_text is None:
            # Re-read existing HTML back into a formatted raw string conserving hard semantic root depths!
            root = self.soup.find(id="root") or self.soup.find("body") or self.soup
            kb_html = str(root)
            generated_html = llm_client.generate_structured_html(kb_html, compress=compress)
        else:
            generated_html = llm_client.generate_structured_html(raw_text, compress=compress)

        # Drop the AI generation cleanly into active memory wrapper natively 
        self.soup = BeautifulSoup(generated_html, "lxml")
        
        # Divert to the central node tracker securing validation loops inherently
        return self._finalize_and_sync(llm_client, hierarchical=True)

    @trace_timing
    def _sectionize(self):
        """
        Deterministic post-processor that converts flat heading+content sibling
        sequences into nested <section> blocks.
        
        Before: <body> <h1> <h2> <p> <p> <h3> <p> <h2> <p> </body>
        After:  <body> <section><h1> <section><h2> <p> <p> <section><h3> <p></section></section> <section><h2> <p></section></section></body>
        
        Must run BEFORE finalize_atomization() so sections get deterministic IDs.
        """
        # TODO: bounding ul with p
        container = self.soup.find(id="root") or self.soup.find("body")
        if not container:
            return
        self._wrap_heading_level(container, 1)

    def _wrap_heading_level(self, parent, level):
        """
        Groups direct children of `parent` that are headed by <hN> into <section> tags.
        Recurses into each created section for the next heading level.
        """
        if level > 6:
            return

        h_tag = f"h{level}"

        # Check if there are any direct-child headings at this level
        if not parent.find_all(h_tag, recursive=False):
            # No headings at this level — try next level down
            self._wrap_heading_level(parent, level + 1)
            return

        # Extract all direct children from the tree (detach)
        children = list(parent.children)
        for child in children:
            child.extract()

        current_section = None

        for child in children:
            is_heading = hasattr(child, 'name') and child.name == h_tag
            is_already_section = hasattr(child, 'name') and child.name == 'section'

            if is_heading:
                # Start a new section for this heading
                current_section = self.soup.new_tag("section")
                parent.append(current_section)
                current_section.append(child)
            elif is_already_section:
                # Already wrapped — append as-is, don't double-wrap
                parent.append(child)
                current_section = None
            elif current_section is not None:
                # Content belonging to the current heading's section
                current_section.append(child)
            else:
                # Preamble content before any heading at this level
                parent.append(child)

        # Recurse into each created section for the next heading level
        for section in parent.find_all("section", recursive=False):
            self._wrap_heading_level(section, level + 1)

    @trace_timing
    def _finalize_and_sync(self, llm_client, hierarchical=False):
        """
        Synchronizes structural DOM edits back onto the physical KB.
        1. Sectionize flat headings into nested <section> blocks
        2. Assign deterministic IDs to all nodes
        3. Trigger vector rebuilding
        """
        # Enforce hierarchical DOM structure before ID assignment
        self._sectionize()

        finalized_html = self.finalize_atomization(str(self.soup))
        self.soup = BeautifulSoup(finalized_html, "lxml")
        self.save_kb(finalized_html)

        all_active_ids = [p['id'] for p in self.soup.find_all('p') if p.get('id') and p.get_text(strip=True)]

        if hierarchical:
            self.sync_embeddings_hierarchical(llm_client, all_active_ids)
        else:
            self.sync_embeddings(llm_client, all_active_ids)

        return all_active_ids


    @trace_timing
    def rewrite(self, selector: str, updated_content: str):
        """
        Safely swaps interior content of an existing node, or splices new blocks globally.
        Matches node via CSS selector path (e.g. 'html > body > p#p-123').
        """
        print(f"[MemoryManager.rewrite] Applying DOM mutation hook onto tag '{selector}'...")
        
        target = None
        if selector:
            if '#' in selector and len(selector.split('#')) == 2:
                # Direct lookup natively to bypass BeautifulSoup CSS parser breaking on invalid selector dots/spaces!
                tag_name, tag_id = selector.split('#')
                target = self.soup.find(tag_name, id=tag_id)
            else:
                try:
                    target = self.soup.select_one(selector)
                except Exception:
                    pass
        
        # Parse the new block explicitly 
        new_tag_source = BeautifulSoup(updated_content, "html.parser")
        
        # Ensure we don't accidentally graft a whole text-doc. Extract the active node:
        new_nodes = [n for n in new_tag_source.children if n.name]
        
        if target and new_nodes:
            # Replace the whole parent natively
            target.replace_with(new_nodes[0])
            return True
            
        # Upsert grafting: If this is a structural element entirely new to the graph, 
        # seamlessly attach it to the primary graph tree root natively!
        root_container = self.soup.find(id="root") or self.soup.find("body")
        if root_container and new_nodes:
            for node in new_nodes:
                root_container.append(node)
            return True
            
        return False


    def _generate_deterministic_id(self, text: str, prefix: str = 'p') -> str:
        """
        Generates a stable ID based on the text content.
        If the text is the same, the ID will always be the same.
        """
        # Create a SHA-256 hash of the text
        hash_digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
        # Use the first 12 characters for a clean localized physical ID
        return f"{prefix}-{hash_digest[:12]}"

    @trace_timing
    def finalize_atomization(self, generated_html: str):
        """
        Processes the AI's HTML, ensuring every node has a stable, manual ID organically!
        """
        soup = BeautifulSoup(generated_html, "lxml")
        
        structural_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section', 'div', 'main', 'span', 'b', 'strong', 'i', 'em', 'u']
        # Find all tags that don't have an 'id' attribute natively mapped
        for tag in soup.find_all(structural_tags, id=False):
            if tag.get_text(strip=True):
                # Generate ID from the content itself binding explicitly onto its tag wrapper name prefix
                stable_id = self._generate_deterministic_id(tag.get_text(), prefix=tag.name)
                tag['id'] = stable_id
            
        return soup.prettify()

    @trace_timing
    def save_kb(self, content):
        """Persists the BeautifulSoup object to the HTML file."""
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, "w", encoding="utf-8") as f:
            f.write(content)



    # get all p contents
    @trace_timing
    def get_all_p_contents(self):
        """Returns a map of {selector_id: text_content} for all p tags."""
        return {p['id']: p.get_text() for p in self.soup.find_all('p')}
    
    def _get_structural_lineage(self, tag):
        """
        Returns the top-down list of structural ancestor tags (filtered to STRUCTURAL_TAGS)
        for a given tag, excluding the tag itself.
        """
        ancestors = []
        for parent in tag.parents:
            if parent.name and parent.name in self.STRUCTURAL_TAGS and parent.get('id'):
                ancestors.append(parent)
        ancestors.reverse()  # top-down order
        return ancestors

    def _build_selector_path(self, tag):
        """Builds the CSS selector path string for a tag."""
        parents = list(tag.parents)
        path_parts = []
        for p in reversed(parents):
            if p.name and p.name != '[document]':
                if p.get('id'):
                    path_parts.append(f"{p.name}#{p.get('id')}")
                else:
                    path_parts.append(p.name)
        path_parts.append(f"{tag.name}#{tag.get('id')}")
        return " > ".join(path_parts)

    @trace_timing
    def sync_embeddings_hierarchical(self, llm_client, active_ids):
        """
        Full top-down hierarchical embedding rebuild.
        Called only during atomizer (init + day change).
        Batch-embeds all unique structural ancestors + p tags in one LLM call,
        then sums vectors top-down using memoization.
        """
        print("[MemoryManager.sync_embeddings_hierarchical] Building hierarchical structural vectors...")
        from datetime import datetime

        structural_cache = {}  # tag_id -> summed vector (numpy array)
        texts_to_embed = {}    # tag_id -> text (ordered dict for batch)
        lineage_cache = {}     # tag_id -> list of ancestor tags (memoized)

        def get_lineage(tag):
            tid = tag.get('id')
            if tid not in lineage_cache:
                lineage_cache[tid] = self._get_structural_lineage(tag)
            return lineage_cache[tid]

        # Phase 1: Scan all p tags, collect all unique nodes needing raw embeddings
        p_tags = []
        for p_id in active_ids:
            tag = self.soup.find(id=p_id)
            if not tag:
                continue
            p_tags.append((p_id, tag))
            lineage = get_lineage(tag)

            # Collect structural ancestors
            for ancestor in lineage:
                aid = ancestor.get('id')
                if aid and aid not in texts_to_embed:
                    texts_to_embed[aid] = ancestor.get_text()

            # Collect the p tag itself
            if p_id not in texts_to_embed:
                texts_to_embed[p_id] = tag.get_text()

        if not texts_to_embed:
            return

        # Phase 2: Batch-generate all raw embeddings in ONE API call
        batch_ids = list(texts_to_embed.keys())
        batch_texts = [texts_to_embed[tid] for tid in batch_ids]
        print(f"[Hierarchical] Batch embedding {len(batch_texts)} nodes ({len(active_ids)} p-tags + {len(batch_texts) - len(active_ids)} structural ancestors)")
        raw_vectors = llm_client.generate_embeddings(batch_texts)

        raw_embeddings = {}  # tag_id -> raw numpy vector
        for i, tid in enumerate(batch_ids):
            raw_embeddings[tid] = np.array(raw_vectors[i], dtype='float32')

        # Phase 3: Top-down memoized summation for each p tag
        p_embedding_map = {}
        for p_id, tag in p_tags:
            lineage = get_lineage(tag)
            full_chain = lineage + [tag]  # ancestors + p itself

            for node in full_chain:
                nid = node.get('id')
                if nid in structural_cache:
                    continue  # already memoized

                raw = raw_embeddings.get(nid)
                if raw is None:
                    continue

                # Find immediate structural parent
                parent_ancestors = get_lineage(node)
                if parent_ancestors:
                    parent_id = parent_ancestors[-1].get('id')
                    if parent_id and parent_id in structural_cache:
                        structural_cache[nid] = raw + structural_cache[parent_id]
                    else:
                        structural_cache[nid] = raw  # parent not cached, use raw
                else:
                    structural_cache[nid] = raw  # root node, no parent

            # The p tag's final vector is the summed vector in structural_cache
            if p_id in structural_cache:
                p_embedding_map[p_id] = {
                    "selector": self._build_selector_path(tag),
                    "vector": structural_cache[p_id].tolist(),
                    "last_consolidated": datetime.now().isoformat()
                }

        # Phase 4: Persist p embeddings
        os.makedirs(os.path.dirname(self.p_embeddings_path), exist_ok=True)
        with open(self.p_embeddings_path, "w") as f:
            json.dump(p_embedding_map, f, indent=4)

        # Phase 5: Persist structural cache (non-p entries only)
        structural_persist = {}
        for sid, vec in structural_cache.items():
            if sid not in active_ids:  # exclude p tags
                structural_persist[sid] = vec.tolist()

        os.makedirs(os.path.dirname(self.structural_embeddings_path), exist_ok=True)
        with open(self.structural_embeddings_path, "w") as f:
            json.dump(structural_persist, f, indent=4)

        print(f"[Hierarchical] Persisted {len(p_embedding_map)} p-vectors, {len(structural_persist)} structural vectors")

    @trace_timing
    def sync_embeddings(self, llm_client, active_ids):
        """
        Lightweight stage-update path.
        Reads cached structural vectors from structural_embeddings.json (read-only)
        and sums them with new p-tag raw embeddings.
        """
        print("[MemoryManager.sync_embeddings] Stage-update: syncing with structural cache...")
        from datetime import datetime

        # 1. Load existing p embedding map
        embedding_map = {}
        if os.path.exists(self.p_embeddings_path):
            with open(self.p_embeddings_path, "r") as f:
                try:
                    embedding_map = json.load(f)
                except json.JSONDecodeError:
                    pass

        # 2. Load structural cache (read-only)
        structural_cache = {}
        if os.path.exists(self.structural_embeddings_path):
            with open(self.structural_embeddings_path, "r") as f:
                try:
                    structural_cache = json.load(f)
                except json.JSONDecodeError:
                    pass

        # 3. Prune dead p selectors
        if isinstance(embedding_map, dict):
            dead_nodes = [k for k in embedding_map.keys() if k not in active_ids]
            for key in dead_nodes:
                del embedding_map[key]

        # 4. Collect new p tags that need embedding
        new_nodes = []
        new_contents = []
        new_selectors = []
        new_parent_ids = []  # nearest structural parent ID for each new p

        for p_id in active_ids:
            if p_id not in embedding_map:
                tag = self.soup.find(id=p_id)
                if tag:
                    new_nodes.append(p_id)
                    new_contents.append(tag.get_text())
                    new_selectors.append(self._build_selector_path(tag))

                    # Find nearest structural parent in cache
                    lineage = self._get_structural_lineage(tag)
                    parent_id = None
                    for ancestor in reversed(lineage):  # closest first
                        aid = ancestor.get('id')
                        if aid and aid in structural_cache:
                            parent_id = aid
                            break
                    new_parent_ids.append(parent_id)

        # 5. Generate raw embeddings for new p tags and sum with parent vectors
        if new_nodes:
            vectors = llm_client.generate_embeddings(new_contents)
            for i, p_id in enumerate(new_nodes):
                raw_vec = np.array(vectors[i], dtype='float32')

                parent_id = new_parent_ids[i]
                if parent_id and parent_id in structural_cache:
                    parent_vec = np.array(structural_cache[parent_id], dtype='float32')
                    final_vec = (raw_vec + parent_vec).tolist()
                else:
                    final_vec = raw_vec.tolist()

                embedding_map[p_id] = {
                    "selector": new_selectors[i],
                    "vector": final_vec,
                    "last_consolidated": datetime.now().isoformat()
                }

        # 6. Flush p embeddings
        os.makedirs(os.path.dirname(self.p_embeddings_path), exist_ok=True)
        with open(self.p_embeddings_path, "w") as f:
            json.dump(embedding_map, f, indent=4)

    @trace_timing
    def keyword_search(self, query: str):
        """
        Traditional keyword search of the query among KB html.
        Tokenizes the query and finds nodes containing any of the keywords.
        Returns: List of hit IDs matching keywords.
        """
        print("[MemoryManager.keyword_search] Performing traditional keyword search...")
        if not self.soup:
            return []

        import re
        # Tokenize query: lowercase, alphanumeric words > 2 chars, filter stop words
        stop_words = {'the', 'and', 'are', 'was', 'for', 'that', 'this', 'with', 'from', 'your', 'have', 'has', 'had', 'but', 'not', 'can', 'will'}
        tokens = [t.lower() for t in re.findall(r'\b\w+\b', query) if len(t) > 2]
        keywords = set([t for t in tokens if t not in stop_words])
        
        if not keywords:
            return []

        hit_scores = {}
        for tag in self.soup.find_all(True): # Search for all tags not only p
            if tag.get('id') and tag.get_text(strip=True):
                text_lower = tag.get_text().lower()
                # Count how many keywords appear in the text
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > 0:
                    hit_scores[tag['id']] = score
                    
        # Sort by most keyword matches
        sorted_hits = sorted(hit_scores.keys(), key=lambda k: hit_scores[k], reverse=True)
        return sorted_hits

    @trace_timing
    def semantic_search(self, query_vector, threshold=0.80): # threshold is given with brain.search_threshold
        """
        Compares query vector against all P-embeddings.
        Returns: List of hit IDs that pass the threshold.
        """
        print("[MemoryManager.semantic_search] Traversing dense node space globally...")
        if not os.path.exists(self.p_embeddings_path):
            return []

        # TODO: maybe other than p tags?
        with open(self.p_embeddings_path, "r") as f:
            embedding_map = json.load(f)

        if not embedding_map:
            return []

        # 1. Prepare data for NumPy
        ids = list(embedding_map.keys())
        vectors = np.array([item['vector'] for item in embedding_map.values()], dtype='float32')
        q_vec = np.array(query_vector, dtype='float32')

        # Short-circuit: zero-norm query can never match anything
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        # 2. Vectorized Cosine Similarity
        dot_product = np.dot(vectors, q_vec)
        norms = np.linalg.norm(vectors, axis=1) * q_norm
        norms = np.where(norms == 0, 1e-10, norms)
        similarities = dot_product / norms

        # 3. Filter by threshold
        mask = similarities >= threshold
        return [ids[i] for i in np.where(mask)[0]]
