import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from google.genai import types
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


class LangChainClient:
    @trace_timing
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            #model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1
        )
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            output_dimensionality=256
        )
        # # Local embedding model
        # self.embedding_model = HuggingFaceEmbeddings(
        #     model_name="jinaai/jina-embeddings-v5-text-small",
        #     model_kwargs={'trust_remote_code': True},
        #     encode_kwargs={'task': 'retrieval', 'truncate_dim': 256}
        # )

    @trace_timing
    def _get_clean_response(self, system_prompt: str, human_prompt: str) -> str:
        """Unified invocation and extraction logic across all inference modes."""
        sys_msg = SystemMessage(content=system_prompt)
        hum_msg = HumanMessage(content=human_prompt)
        
        response = self.model.invoke([sys_msg, hum_msg])
        
        raw_content = response.content
        if isinstance(raw_content, list):
            raw_content = next((block["text"] for block in raw_content if isinstance(block, dict) and "text" in block), str(raw_content))
            
        content = raw_content.replace('```html', '').replace('```', '').strip()
        return content

    @trace_timing
    def generate_structured_html(self, raw_text: str, compress: bool = False) -> str:
        """
        Uses the LLM to convert raw text into a structured HTML document
        optimized for the downstream embedding and retrieval pipeline.
        
        Critical contract: The engine indexes ONLY <p> tags as retrieval units.
        Every <p> must contain a single coherent concept for effective semantic search.
        """
        if compress:
            system_prompt = """You are restructuring an existing HTML knowledge base for long-term storage efficiency.

INPUT: An HTML document that has grown organically over multiple sessions.
OUTPUT: A reorganized HTML document with improved logical grouping.

STRUCTURE RULES:
1. Use <h1>, <h2>, <h3> headers to create a clear topical hierarchy.
2. ALL content must be strictly nested inside its semantic parent. Wrap each heading and ALL of its associated content (<p>, <ul>, <ol>, <table>, etc.) in a <section> tag. Nest sections hierarchically: h3-sections inside h2-sections inside h1-sections. Nothing should float as an orphan sibling of a heading it belongs to.
3. Each <p> tag must contain exactly one coherent concept or fact. This is critical — downstream systems use individual <p> tags as atomic retrieval units for semantic search.
4. Lists (<ul>/<ol>) must be placed inside the <section> of the heading they relate to, after any introductory <p> tag.
5. Merge duplicate or near-duplicate information. When facts conflict, the most recently added version takes priority.
6. Preserve the substantive content. Do not aggressively summarize — reorganize and deduplicate.
7. Do NOT add id attributes. The engine assigns deterministic IDs automatically.
8. Return only clean HTML markup. No markdown, no code fences."""
            human_message = f"Restructure and deduplicate the following knowledge base HTML:\n\n{raw_text}"
        else:
            system_prompt = """You are converting unstructured text into a well-organized HTML document.

INPUT: Raw, unstructured text containing various concepts and facts.
OUTPUT: A clean HTML document with logical structure.

STRUCTURE RULES:
1. Organize content hierarchically using <h1>, <h2>, <h3> for topics and subtopics.
2. ALL content must be strictly nested inside its semantic parent. Wrap each heading and ALL of its associated content (<p>, <ul>, <ol>, <table>, etc.) in a <section> tag. Nest sections hierarchically: h3-sections inside h2-sections inside h1-sections. Nothing should float as an orphan sibling of a heading it belongs to.
3. Each <p> tag must contain exactly one coherent concept or fact. This is critical — downstream systems use individual <p> tags as atomic retrieval units for semantic search. Break large blocks into multiple <p> tags.
4. Lists (<ul>/<ol>) belong inside the <section> of the heading they relate to, after any introductory <p> tag. Example: <section><h3>Features</h3><p>Key features include:</p><ul><li>...</li></ul></section>
5. Preserve all original content and its semantic meaning. Do not omit or summarize.
6. When contradictions exist in the source text, keep the latest version.
7. Do NOT add id attributes. The engine assigns deterministic IDs automatically.
8. Return only clean HTML markup. No markdown, no code fences."""
            human_message = f"Convert the following text into structured HTML:\n\n{raw_text}"
            
        return self._get_clean_response(system_prompt, human_message)


    @trace_timing
    def synthesize_session(self, log_history: list, context_html: str) -> str:
        """
        Merges an active Stage Log (conversation buffer) into the anchoring KB context,
        producing updated or new HTML fragments for DOM grafting.
        """
        history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in log_history] if isinstance(log_history, list) else log_history)
        
        system_prompt = """You are merging new knowledge from a conversation into existing HTML knowledge fragments.

INPUT:
- "Original HTML context": Existing HTML fragments from the knowledge base that are topically relevant to the conversation.
- "Conversation log": A sequence of Q&A pairs containing new information to integrate.

OUTPUT: Updated or new HTML fragments ready for DOM insertion.

RULES:
1. If new knowledge fits into the provided Original HTML fragments, rewrite the ENTIRE fragment incorporating the new information. Preserve the original id attributes on parent tags you did not change textually.
2. If the new knowledge is unrelated to any provided fragment, create a NEW standalone <section> with appropriate headings and content.
3. ALL content must be strictly nested inside its semantic parent. Wrap each heading and ALL of its associated content (<p>, <ul>, <ol>, etc.) in a <section> tag. Lists and supporting elements belong inside the section of their heading, not as orphan siblings.
4. Each <p> tag must contain exactly one coherent concept — these are the atomic retrieval units for semantic search.
5. For any content you rewrite or create new, do NOT include id attributes — the engine assigns them automatically based on content hashing. Only preserve ids on tags whose text you kept unchanged.
6. Output ONLY raw HTML tags. No full <html>/<body> wrapper. No markdown. No commentary."""
        human_message = f"Original HTML context:\n{context_html}\n\nConversation log:\n{history_str}"
        return self._get_clean_response(system_prompt, human_message)


    @trace_timing
    def generate_embeddings(self, text: list):
        """Batch-generates embeddings for semantic indexing."""
        return self.embedding_model.embed_documents(text)

    @trace_timing
    def generate_response(self, query: str, context: str, history: list, session_history: list = None) -> str:
        """
        Generates a conversational response using the model's own knowledge,
        supplemented by retrieved long-term memory and short-term conversation context.
        """
        print("[LangChainClient.generate_response] Generating response...")
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in history]) if history else ""
        session_history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in session_history]) if session_history else ""

        system_prompt = f"""You are an intelligent conversational assistant. Answer the user's questions using your full general knowledge.

You also have access to supplementary memory sources that may contain relevant context from past interactions. Use them naturally — like a person recalling relevant memories — but they are not your only source of knowledge. If the user asks something outside of what's stored in memory, answer freely from your own understanding.

Long-term memory (retrieved from knowledge base, might be entirely irrelevant):
{context if context else "(No relevant memories retrieved)"}

Recent conversation context (current topic buffer):
{history_str if history_str else "(New conversation regarding this topic)"}"""

        messages = [SystemMessage(content=system_prompt)]
        
        # Replay recent session turns as message pairs for continuity
        if session_history:
            for item in session_history:
                messages.append(HumanMessage(content=item['query']))
                messages.append(AIMessage(content=item['response']))
                
        messages.append(HumanMessage(content=query))
        try:
            response = self.model.invoke(messages)
            content = response.content
            
            # Normalize multi-modal output blocks into a continuous string
            if isinstance(content, list):
                text_blocks = []
                for block in content:
                    if isinstance(block, dict) and 'text' in block:
                        text_blocks.append(block['text'])
                    elif isinstance(block, str):
                        text_blocks.append(block)
                return "\n".join(text_blocks)
            elif isinstance(content, dict) and 'text' in content:
                return content['text']
            
            return str(content)
        except Exception as e:
            return f"Error: {str(e)}"