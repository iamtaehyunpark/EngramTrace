import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from google.genai import types

class LangChainClient:
    def __init__(self):
        # Initializing Gemini 3.1 Flash-Lite
        self.model = ChatGoogleGenerativeAI(
            model="gemini-flash-latest", # Use 1.5 Flash for the Lite-equivalent speed/efficiency
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1  # Low temperature is critical for structural consistency
        )

        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            output_dimensionality=256
        )

    def generate_structured_html(self, raw_text: str) -> str:
        """
        Uses the LLM to semantically 
        partition raw text into a strictly addressable HTML structure.
        """
        
        system_prompt = SystemMessage(content="""
            Your task is to transform raw, unstructured text into standard HTML.
            
            RULES:
            1. Convert the text into a clean, normal HTML page.
            2. Organize the content naturally using standard HTML tags (e.g., <p>, <h1>, <h2>, <ul>, <li>).
            3. Do NOT add artificial IDs, custom data-attributes, or forced semantic grouping containers unless it's natural.
            4. Return only the HTML markup.
        """)

        human_message = HumanMessage(content=f"Convert the following text into normal HTML formatting:\n\n{raw_text}")

        response = self.model.invoke([system_prompt, human_message])
        
        # Extract string content robustly
        raw_content = response.content
        if isinstance(raw_content, list):
            # Grab the text chunk if it's a list
            raw_content = next((block["text"] for block in raw_content if isinstance(block, dict) and "text" in block), str(raw_content))
            
        # Clean the response in case the model includes markdown formatting (```html)
        content = raw_content.replace('```html', '').replace('```', '').strip()
        return content

    def generate_embeddings(self, text):
        """
        Batch generates embeddings for the retrieved or updated <p> tags.
        """
        return self.embedding_model.embed_documents(text)