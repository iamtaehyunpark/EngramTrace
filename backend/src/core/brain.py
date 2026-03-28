"""
3. The State Manager (brain.py / stage_manager.py)
This manages the "Short-Term" session and determines when a context switch occurs.

CalculateStageSimilarity(query_vec): Compares the current query vector to the average vector of the current_stage_log.json.

ManageStageTransition(): Logic to decide whether to continue the current session or 
    "flush" the log and trigger a consolidation event.

BufferQAPair(query, response): Appends the latest interaction to the Stage Log 
    without touching the Long-Term Knowledge Base yet.

TimeGapHomeostasis(): Checks the timestamp difference between queries to decide if the 
    Day System needs to trigger a global reformat.
"""



"""
4. The Consolidation Engine (brain.py)
This is the "Learning" component where the short-term log is merged into the long-term KB.

SynthesizeStageLog(): Uses Gemini 3.1 Flash-Lite to summarize the current Stage Log 
    into a cohesive set of new "propositions."

IdentifyAnchorPoints(): Matches the summarized log to the most relevant existing selectors 
    in the HTML KB.

RegenerateContext(selector_id, log_summary): An LLM call that rewrites a specific <p> tag 
    by blending its old content with the new information from the Stage Log.

DifferentialReIndexing(affected_ids): Selectively deletes and regenerates vectors in 
    p_embeddings.json only for the changed/added selectors.
"""