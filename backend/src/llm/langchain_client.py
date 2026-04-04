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
            You are summarizing a short-term conversational session and integrating it into Long-Term HTML knowledge.
            
            RULES:
            1. Read the Original HTML and the conversation Dialogue.
            2. Merge any new, valid knowledge from the dialogue directly into the original HTML structures.
            3. Output ONLY the updated HTML. Do not output conversational pre-text.
            4. Retain all semantic parent structure mapping (if it's in a section, keep it in a section).
        """
        human_message = f"Original HTML context:\n{context_html}\n\nDialogue History to apply:\n{history_str}"
        return self._get_clean_response(system_prompt, human_message)


    def generate_embeddings(self, text: list):
        """
        Batch generates embeddings for the retrieved or updated <p> tags.
        """
        return self.embedding_model.embed_documents(text)

    def generate_response(self, query: str, context: str, history: list) -> str:
        """
        Generates a standard cognitive response leveraging both deep structure and ephemeral loops safely.
        """
        print("[LangChainClient.generate_response] Pinging Gemini 3.1 inference matrix...")
        history_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in history] if isinstance(history, list) else history)
        
        system_prompt = """
            You are a helpful answering assistant acting as the inference engine for EngramTrace.
            Use your expansive underlying knowledge to answer the user's latest query as thoroughly and accurately as possible.
            You are provided with Document Context (Long-term Memory) and Dialogue History (Short-term context) to help inform your answer, but you are not restricted by it. Do not state that the context lacks information; just provide the best answer you can natively!
        """
        human_message = f"Long-Term Context:\n{context}\n\nRecent History:\n{history_str}\n\nUser Query: {query}"
        
        # We don't want to strip HTML markdown logic for normal responses, so we will manually invoke
        # However, getting clean response doesn't hurt plain text.
        return self._get_clean_response(system_prompt, human_message)