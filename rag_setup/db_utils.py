#db interaction layer 
import chromadb
import uuid
import pathlib

class ChromaDB: 
    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=pathlib.Path(__file__).parent.parent / "chroma_db")
        self.collection = self.client.get_collection(name=collection_name)
        
    def add_chunks(self, chunks, embeddings, metadatas, ids=None):
        if not ids:
            ids = str(uuid.uuid4())
        self.collection.upsert(documents=chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)

    def search(self, query, n_results=3, filter_param=None):
        if filter_param:
            return self.collection.query(query_texts=[query], n_results=n_results, where=filter_param)
        else:
            return self.collection.query(query_texts=[query], n_results=n_results)
    
    def search_by_embedding(self, query, n_results=3, filter_param=None):
        if filter_param:
            return self.collection.query(query_embeddings=[query], n_results=n_results, where=filter_param)
        else:
            return self.collection.query(query_embeddings=[query], n_results=n_results)

def create_collection(collection_name):
    client = chromadb.PersistentClient(path=pathlib.Path(__file__).parent.parent / "chroma_db")
    collection = client.create_collection(name=collection_name)
    return collection

def delete_collection(collection_name):
    client = chromadb.PersistentClient(path=pathlib.Path(__file__).parent.parent / "chroma_db")
    client.delete_collection(name=collection_name)

def list_collections():
    client = chromadb.PersistentClient(path=pathlib.Path(__file__).parent.parent / "chroma_db")
    return client.list_collections()

if __name__ == "__main__":
    # print(list_collections())
    create_collection("document_summary")
    create_collection("document_chunks")
    print(list_collections())
    # delete_collection("document_summary")
    # delete_collection("document_chunks")
    # print(list_collections())