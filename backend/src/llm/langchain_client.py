"""
LangChain integration for Phase I (Ingestion / Synaptic Folding) and Phase III (Inference).
Uses LangChain with Gemini 3.1 Flash-Lite for triplet extraction and Gemini Embedding for Synaptic Embeddings.
"""
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

load_dotenv()

class LangChainLLMClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
    def generate_synaptic_embedding(self, text: str):
        """Calculates E_edge = Embed(Source.text + Relation.text + Target.text) using LangChain embeddings."""
        embedding_model = GoogleGenerativeAIEmbeddings(model_name="gemini-embedding-001", api_key=self.api_key, output_dimensionality=768)
        return embedding_model.embed_query(text)
