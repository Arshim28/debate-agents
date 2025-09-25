from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

class GeminiEmbedding:
    def __init__(self, api_key, embedding_dimensions=768, embedding_model="gemini-embedding-001"):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.embedding_dimensions = embedding_dimensions
        self.embedding_model = embedding_model

    def embed(self, text, task_type="retrieval_document"):
        if isinstance(text, str):
            # Single text input
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768
                )
            )
            return response.embeddings[0].values
        elif isinstance(text, list):
            # Batch processing for multiple texts with 100-item limit
            all_embeddings = []
            batch_size = 100
            
            for i in range(0, len(text), batch_size):
                batch = text[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(text) + batch_size - 1)//batch_size} ({len(batch)} items)")
                
                response = self.client.models.embed_content(
                    model=self.embedding_model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=768
                    )
                )
                
                # Extract embeddings from batch response
                batch_embeddings = [emb.values for emb in response.embeddings]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        else:
            raise ValueError("Input must be a string or list of strings")

if __name__ == "__main__":
    load_dotenv()
    gemini_embedding = GeminiEmbedding(api_key=os.getenv("GEMINI_API_KEY"))
    # with open("debug/prepped_data.json", "r") as f:
    #     prepped_data = json.load(f)
    # chunks = prepped_data["summary"]
    # chunks_embeddings = gemini_embedding.embed(chunks)
    chunks_embeddings = gemini_embedding.embed("Hello, world!")
    print(chunks_embeddings)
    