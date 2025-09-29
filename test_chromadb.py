#!/usr/bin/env python3
"""
Test script to check ChromaDB content and data connectors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_setup.db_utils import ChromaDB, list_collections
from dotenv import load_dotenv

def check_chromadb_content():
    """Check what's in the ChromaDB collections"""
    print("=== ChromaDB Content Check ===")

    try:
        # List all collections
        collections = list_collections()
        print(f"Available collections: {[c.name for c in collections]}")

        # Check document_summary collection
        try:
            summary_collection = ChromaDB("document_summary")
            # Get a sample to check if there's content
            sample_results = summary_collection.collection.peek(limit=3)
            print(f"\ndocument_summary collection:")
            print(f"  - Count: {summary_collection.collection.count()}")
            if sample_results['documents']:
                print(f"  - Sample document preview: {sample_results['documents'][0][:200]}...")
                print(f"  - Sample metadata: {sample_results['metadatas'][0] if sample_results['metadatas'] else 'None'}")
            else:
                print("  - No documents found")
        except Exception as e:
            print(f"Error accessing document_summary: {e}")

        # Check document_chunks collection
        try:
            chunks_collection = ChromaDB("document_chunks")
            sample_results = chunks_collection.collection.peek(limit=3)
            print(f"\ndocument_chunks collection:")
            print(f"  - Count: {chunks_collection.collection.count()}")
            if sample_results['documents']:
                print(f"  - Sample chunk preview: {sample_results['documents'][0][:200]}...")
                print(f"  - Sample metadata: {sample_results['metadatas'][0] if sample_results['metadatas'] else 'None'}")
            else:
                print("  - No documents found")
        except Exception as e:
            print(f"Error accessing document_chunks: {e}")

    except Exception as e:
        print(f"Error checking ChromaDB: {e}")

def check_required_api_keys():
    """Check what API keys are needed for the connectors"""
    print("\n=== Required API Keys Check ===")

    load_dotenv()

    required_keys = {
        "OPEN_ROUTER_API_KEY": "For data manager routing (Grok model)",
        "YOUTUBE_API_KEY": "For YouTube transcript extraction",
        "JINA_API_KEY": "For web search results",
        "GEMINI_API_KEY": "For embeddings and RAG retrieval",
        "MISTRAL_API_KEY": "For PDF-to-markdown conversion (if not using existing ChromaDB)"
    }

    print("Checking environment variables:")
    for key, description in required_keys.items():
        value = os.getenv(key)
        status = "✓ SET" if value else "✗ MISSING"
        print(f"  {key}: {status} - {description}")

if __name__ == "__main__":
    check_chromadb_content()
    check_required_api_keys()