import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag_setup.db_utils import ChromaDB
from rag_setup.gemini_embedding import GeminiEmbedding

class DataRetriever:
    def __init__(self, summary_collection_name, chunk_collection_name, gemini_api_key):
        self.summary_collection_name = summary_collection_name
        self.chunk_collection_name = chunk_collection_name
        self.summary_collection = ChromaDB(summary_collection_name)
        self.chunk_collection = ChromaDB(chunk_collection_name)
        self.gemini_embedding = GeminiEmbedding(gemini_api_key)

    
    def retrieve_docs(self, query, doc_count=5):
        query_embedding = self.gemini_embedding.embed(query,task_type="RETRIEVAL_QUERY")
        retrieved_docs = self.summary_collection.search_by_embedding(query_embedding, n_results=doc_count)
        return [doc["source"] for doc in retrieved_docs["metadatas"][0]]
        
    def retrieve_chunks(self, query, doc_list, chunk_count=15):
        query_embedding = self.gemini_embedding.embed(query,task_type="RETRIEVAL_QUERY")
        retrieved_chunks = self.chunk_collection.search_by_embedding(query_embedding, n_results=chunk_count, filter_param={"source": {"$in": doc_list}})
        return retrieved_chunks["documents"][0]
    
    def retrieve(self, query, chunk_count=5, doc_count=3):
        docs = self.retrieve_docs(query, doc_count)
        chunks = self.retrieve_chunks(query, docs, chunk_count)
        return chunks

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    local_docs_connector = DataRetriever("document_summary", "document_chunks", os.getenv("GEMINI_API_KEY"))
    chunks = local_docs_connector.retrieve("What is the outlook of indian IT sector after the AI boom?")
    print(chunks)
