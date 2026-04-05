import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from google.genai import types

class LangChainClient:
    def __init__(self):
        # Initializing Gemini 3.1 Flash-Lite
        self.model = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1  # Low temperature is critical for structural consistency
        )

        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            output_dimensionality=256
        )

    def _get_clean_response(self, system_prompt: str, human_prompt: str) -> str:
        """Utility to unify the invocation and extraction logic safely across all inference modes."""
        sys_msg = SystemMessage(content=system_prompt)
        hum_msg = HumanMessage(content=human_prompt)
        
        response = self.model.invoke([sys_msg, hum_msg])
        
        raw_content = response.content
        if isinstance(raw_content, list):
            raw_content = next((block["text"] for block in raw_content if isinstance(block, dict) and "text" in block), str(raw_content))
            
        content = raw_content.replace('```html', '').replace('```', '').strip()
        return content

    def generate_structured_html(self, raw_text: str, compress: bool = False) -> str:
        """
        Uses the LLM to semantically partition raw text into a strictly addressable HTML structure.
        """
        if compress:
            system_prompt = """
                Your task is to aggressively format and compress a large temporal Knowledge Base into a tightly organized, summarized HTML document.
                RULES:
                1. Chronologically compress, summarize, or discard completely outdated or irrelevant conversational noise explicitly.
                2. Consolidate logic tightly utilizing hierarchical headers and standard tags (<p>, <h1>, <h2>).
                3. Do NOT add artificial IDs, custom data-attributes, or forced semantic containers.
                4. Return only the highly optimized, clean HTML markup.
            """
            human_message = f"Compress and format the following textual history into synthesized HTML:\n\n{raw_text}"
        else:
            system_prompt = """
                Your task is to transform raw, unstructured text into standard HTML.
                RULES:
                1. Convert the text into a clean, normal HTML page.
                2. Organize the content naturally using standard HTML tags (e.g., <p>, <h1>, <h2>, <ul>, <li>).
                3. Do NOT add artificial IDs, custom data-attributes, or forced semantic grouping containers unless it's natural.
                4. Return only the HTML markup.
            """
            human_message = f"Convert the following text into normal HTML formatting:\n\n{raw_text}"
            
        return self._get_clean_response(system_prompt, human_message)

    def regenerate_structured_html(self, raw_html: str) -> str:
        """
        Restructures messy or broken HTML into clean standard HTML.
        """
        system_prompt = """
            Your task is to repair and standardize existing HTML structures.
            RULES:
            1. Return only clean, normalized HTML.
            2. Keep all text content intact.
            3. Remove orphaned or malformed nested tags but preserve structural meaning.
        """
        human_message = f"Clean the following HTML:\n\n{raw_html}"
        return self._get_clean_response(system_prompt, human_message)


    def synthesize_session(self, log_history: list, context_html: str) -> str:
        """
        Compresses an active Stage Log against its anchoring KB context, creating an updated HTML block proposition.
        """
        # Convert dictionary list string
        history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in log_history] if isinstance(log_history, list) else log_history)
        
        system_prompt = """
            You are a backend graph compiler integrating a short-term conversational session into Long-Term HTML knowledge arrays.
            
            RULES:
            1. You are provided with specific Original HTML structural blocks (parent tags) and a Dialogue History.
            2. If new knowledge fits into the provided Original HTML blocks, rewrite the ENTIRE block incorporating the new knowledge. You MUST preserve the exact original ID attributes of the top-level parent tags.
            3. If the new knowledge is completely unrelated to the provided blocks, create a completely NEW standalone HTML parent tag (like <section> or <article>) for it.
            4. Do not attempt to build a perfectly valid full <html> or <body> document. It is perfectly fine to output disconnected, fragmented HTML tags. They will be grafted structurally by the engine later.
            5. Output ONLY the raw updated HTML tags. Do not output conversational pre-text or markdown borders.
        """
        human_message = f"Original HTML context:\n{context_html}\n\nDialogue History to apply:\n{history_str}"
        return self._get_clean_response(system_prompt, human_message)


    def generate_embeddings(self, text: list):
        """
        Batch generates embeddings for the retrieved or updated <p> tags.
        """
        return self.embedding_model.embed_documents(text)

    def generate_response(self, query: str, context: str, history: list, session_history: list = None) -> str:
        """
        Generates a standard cognitive response leveraging both deep structure and ephemeral loops safely.
        """
        print("[LangChainClient.generate_response] Pinging Gemini 3.1 inference matrix...")
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in history]) if history else "None"
        
        system_prompt = f"""You are a helpful, intelligent AI assistant.
Answer the user's questions utilizing your expansive knowledge freely.
The 'Retrieved Knowledge Base Context' below is just a helpful hint from your long-term memory graph; 
if the user asks something outside of it, you should still answer it using your own general knowledge.

Retrieved Knowledge Base Context (Topical Hints):
{context}

Active Stage Interaction Log (Supplementary Immediate Discussion Focus):
{history_str}
"""
        messages = [SystemMessage(content=system_prompt)]
        
        # Sequentially map the active continuous session status to prevent topical amnesia 
        if session_history:
            for item in session_history:
                messages.append(HumanMessage(content=item['query']))
                messages.append(AIMessage(content=item['response']))
                
        messages.append(HumanMessage(content=query))
        
        response = self.model.invoke(messages)
        
        return response.content