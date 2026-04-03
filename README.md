# EngramFlow (Project OpenMind)

A non-parametric memory architecture that mimics human learning by updating a Synaptic Knowledge Graph instead of model parameters.


## Blueprint: HTML Engram Flow

### Structure
*   **Model:** Gemini 3.1 Flash-Lite (Reading, Generating, Summarizing), Gemini Embedding 1, Langchain
*   **Document (The Knowledge Base):** A strictly formatted HTML file. Text is divided into frequent `<p>` tags to maintain granular "Virtual Nodes," maintaining the hierarchical structure of the context.
*   **Virtual Graph:** A conceptual network where each HTML selector acts as a node. Relationships are implicit via the DOM hierarchy.
*   **Root Anchor:** The highest selector in the HTML (e.g., `<html>` or `<main id="root">`), representing the global context.
*   **P-Embeddings:** Vectors generated for each `<p>` tag, encompassing all content within that specific selector.
*   **Engram Trace:** Retrieved relevant to query context selectors list.
*   **Working Page:** A temporal, minimized version of the HTML Knowledge Base. It contains only the content of the selectors in Engram Trace, retrieved during the current search.
*   **Stage Log:** A temporary stack of Q&A pairs from the current session used for immediate conversational context.

### Data Structure
*   **Virtual Nodes:** Every tag/selector in the HTML is considered a node. Each possesses a summary of its underlying content.
*   **P-Embeddings List:** `List[(selector_path, embedding_vec)]` for all `<p>` tags.
*   **Stage State:** `(Stage_ID, Day_Count)`.
*   **Working Stage Log:** A sequential list of `(Query, Answer)` pairs generated during the current active stage.

### 🔄 Pipeline

#### 1. Initialization
*   **Automated Formatting:** The model organizes raw context into the HTML KB. Every non-leaf selector receives a short summary of its children.
*   **Initial Indexing:** P-Embeddings are generated for every `<p>` tag and stored in the list.

#### 2. Retrieval & Inference (In-Stage)
*   **Similarity Check:** When a query arrives, its embedding `$\vec{q}$` is compared against:
    1.  The P-Embeddings list (to find KB context).
    2.  The previous query/Stage Log (to check for stage continuity).
*   **Ecphory:** If the stage remains the same, the system retrieves relevant `<p>` tags, backtracks their selector paths to the root, and assembles the Working Page (Engram Trace).
*   **Inference:** The model generates an answer using the Working Page + the Stage Log + its own reasoning.
*   **Buffering:** The new Q&A pair is added to the Stage Log. P-Embeddings are not updated yet.

#### 3. Stage Transition & Update (Consolidation)
*   **Trigger:** If `$\text{cos\_sim}(\vec{q}, \vec{prev_q}) < \text{threshold}$`, the Stage is updated.
*   **P-Update Process:**
    *   **Gather:** The current working page and the Engram Trace will be updated first.
    *   **Summarize:** The model merges(updates/generates) the retrieved Working Page with the Stage Log.
    *   **Merge:** The original HTML KB is updated by replacing/modifying the affected `<p>` tags with the newly integrated content by merging 2’s updated working page(summary) with the original HTML KB.
    *   **Re-index:** Delete stale P-Embeddings for affected selectors and generate new vectors for the modified(or newly added) content.

#### 4. Day System (Homeostasis)
*   **Time-Gap Check:** If `$t_{current} - t_{last} > n\text{ hours}$` and a Stage Change is triggered, the Day System activates.
*   **Reformatting:** The entire HTML file is reformatted. Older data is compressed/summarized while more weight is given to the most recent "Day" of Q&A pairs.

### 🔍 Retrieval & Search Logic
1.  **Embed:** `$\vec{q} = Embed{Query}$`.
2.  **Match:** Find all `$P_i$` where `$\text{sim}(\vec{q}, \text{Embed}_{P_i}) > \text{threshold}$`.
3.  **Trace:** Use the selector path (e.g., `body > div#sec1 > p#p42`) to highlight all parent nodes.
4.  **Extract:** Pull text content from retrieved tags into the Engram Trace.

### 🚀 Technical Summary
By treating the Stage as a session-based buffer, the system "thinks" quickly in the short term but "consolidates" carefully in the long term. This prevents the HTML Knowledge Base from becoming cluttered with redundant or irrelevant conversational noise until it is logically confirmed that a topic has concluded.

---

## 🏗 EngramTrace Blueprint Implementation Roadmap

This document outlines the abstract steps to fulfill the **HTML Engram Flow Blueprint** and audits our current project files against that vision.

### 🔄 1. Initialization Phase
*Goal: Turn unstructured text into the structured HTML Virtual Graph and produce base vectors.*

**Abstract Steps:**
1.  **Format Input:** Pass text to an LLM to generate semantic HTML blocks (`<p>` tags wrapping distinct concepts).
2.  **Ensure Graph Integrity:** Assign deterministic unique IDs to all valid `<p>` nodes.
3.  **Embed Storage:** Generate and store dense vectors for all new `<p>` elements into a JSON pairing dictionary, utilizing element structural paths (e.g. `html > body > p#xyz`) as context anchors.

**Current Status:** ✅ **Completed** 
- `langchain_client.generate_structured_html()` successfully instructs the LLM to format content into native DOM structures.
- `MemoryManager.atomizer` and `finalize_atomization` successfully enforce deterministic hashes for every `<p>` tag natively.
- `MemoryManager.sync_embeddings` successfully executes batch vector embedding mapping securely to selector keys in `p_embeddings.json`.

---

### 🔍 2. Retrieval & Inference (In-Stage)
*Goal: Answer user queries rapidly using short-term Buffer Logs and structurally pruned Working Pages.*

**Abstract Steps:**
1.  **Query Generation:** User submits a prompt which is instantly vector-embedded.
2.  **Continuity Check:** Check Cosine Similarity of the new query against the running `Stage Log` session vector to determine if they are still talking about the same topic.
3.  **Ecphory Tracing:** Run vector similarity search across `p_embeddings.json` to find relevant Long-Term `<p>` tags. Trace their selector strings backward to assemble a high-signal, temporary "Working Page" (Engram Trace).
4.  **Inference:** Feed the model both the Working Page and the Short-Term Stage Log to generate an answer.
5.  **Buffer:** Push the new Query & Answer securely to the Short-Term `Stage Log` array without mutating the HTML KB text natively.

**Current Status:** ✅ **Completed**
- ✅ **Done:** `MemoryManager.semantic_search()` mathematically filters Cosine Similarities natively parsing the matrices.
- ✅ **Done:** `EngramTrace._get_stage_context()` physically isolates parents mapping Ecphory reconstruction into dynamic minimal HTML Wrappers.
- ✅ **Done:** `EngramTrace.BufferQAPair()` pushes transient memory cleanly to `current_stage_log.json`.
- ✅ **Done:** `Brain.run_inference()` coordinates the Ecphory search looping both logs directly to `LangChainClient.generate_response()`.

---

### 🏗️ 3. Stage Transition & Update (Consolidation)
*Goal: Permanently merge the Short-Term context session back into the Long-Term HTML Virtual Graph if the conversation switches topics.*

**Abstract Steps:**
1.  **Drift Detection:** Trigger if user conversation vectors diverge drastically from the current Stage.
2.  **Summarize & Synthesis:** LLM reads the entire Stage Log stack along with the retrieved Working Page array and writes a compressed assimilation.
3.  **Document Diffing:** Deeply replace or graft those summaries natively onto the original source HTML Knowledge Base DOM.
4.  **Re-Indexing:** Delete orphaned or stale `<p>` ID vectors internally, and re-embed the newly injected HTML components using the existing vector framework.

**Current Status:** ✅ **Completed**
- ✅ **Done:** `MemoryManager.sync_embeddings()` natively executes precise array updates overwriting diff JSON natively!
- ✅ **Done:** `EngramTrace._calculate_stage_drift()` calculates active `cos_sim` mathematically triggering the Brain hook when threshold breaches natively.
- ✅ **Done:** `LangChainClient.synthesize_session()` executes specific LLM directives forcing block creation cleanly natively.
- ✅ **Done:** `MemoryManager.rewrite()` formally handles physical node modification—utilizing "Upsert Logic" to dynamically patch brand new structural nodes directly into the DOM tree safely natively!

---

### 🕰️ 4. Day System (Homeostasis)
*Goal: Prevent infinite growth over extreme time scales using batch garbage collection.*

**Abstract Steps:**
1.  **Temporal Trigger:** Catch gaps larger than `t(hours)` upon the next interaction wake.
2.  **Reformat:** Do a deep, massive recursive summarization over the entire HTML file, compressing older hierarchical nested groups into tighter `<p>` arrays without destroying context.

**Current Status:** ✅ **Completed** 
- ✅ **Done:** `brain.py` dynamically catches log temporal decays over 4000+ seconds forcibly triggering cycle boundaries dynamically.
- ✅ **Done:** Explicitly bound a `compress=True` boolean constraint inside LangChain, launching aggressive formatting logic through `atomizer` over legacy strings completely optimizing legacy footprints!
