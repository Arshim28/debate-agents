#!/usr/bin/env python3
"""
Test script for RAG Connector functionality
Tests local documents retrieval and ChromaDB integration
"""

import sys
import os
from dotenv import load_dotenv
import json

def test_direct_rag_connector():
    """Test the RAG connector directly"""
    print("🔍 Testing Direct RAG Connector")
    print("=" * 50)

    try:
        from connectors.local_docs_connector import DataRetriever

        # Initialize with environment variables
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not gemini_api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False

        rag_connector = DataRetriever(
            summary_collection_name="document_summary",
            chunk_collection_name="document_chunks",
            gemini_api_key=gemini_api_key
        )

        # Test queries focused on IT sector
        test_queries = [
            "Indian IT sector Q2 FY26 performance and outlook",
            "Nifty IT index performance vs Nifty 50",
            "AI impact on Indian IT services companies",
            "Technology sector margin trends and cost pressures",
            "Indian IT companies quarterly earnings results"
        ]

        results = {}

        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 Test {i}: {query}")
            print("-" * 30)

            try:
                # Test document retrieval
                docs = rag_connector.retrieve_docs(query, doc_count=3)
                print(f"   📄 Retrieved {len(docs)} documents:")
                for j, doc in enumerate(docs, 1):
                    print(f"      {j}. {doc}")

                # Test chunk retrieval
                chunks = rag_connector.retrieve(query, chunk_count=5, doc_count=3)
                print(f"   📝 Retrieved {len(chunks)} chunks")

                # Show first chunk snippet
                if chunks:
                    first_chunk = chunks[0][:200] + "..." if len(chunks[0]) > 200 else chunks[0]
                    print(f"   📖 First chunk preview: {first_chunk}")

                results[f"test_{i}"] = {
                    "query": query,
                    "docs_count": len(docs),
                    "chunks_count": len(chunks),
                    "docs": docs,
                    "first_chunk_preview": first_chunk if chunks else None
                }

                print("   ✅ Query completed successfully")

            except Exception as e:
                print(f"   ❌ Query failed: {str(e)}")
                results[f"test_{i}"] = {
                    "query": query,
                    "error": str(e)
                }

        # Save results
        with open('outputs/rag_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to outputs/rag_test_results.json")
        return True

    except Exception as e:
        print(f"❌ Direct RAG test failed: {str(e)}")
        return False

def test_chromadb_collections():
    """Test ChromaDB collections directly"""
    print("\n🗄️  Testing ChromaDB Collections")
    print("=" * 50)

    try:
        from rag_setup.db_utils import ChromaDB

        # Test summary collection
        summary_collection = ChromaDB("document_summary")
        summary_count = summary_collection.collection.count()
        print(f"📊 Document Summary Collection: {summary_count} documents")

        # Test chunk collection
        chunk_collection = ChromaDB("document_chunks")
        chunk_count = chunk_collection.collection.count()
        print(f"📝 Document Chunks Collection: {chunk_count} chunks")

        if summary_count > 0 and chunk_count > 0:
            print("✅ ChromaDB collections are populated")

            # Get some sample data
            sample_summaries = summary_collection.collection.get(limit=3)
            print(f"\n📄 Sample document sources:")
            for i, metadata in enumerate(sample_summaries['metadatas'], 1):
                source = metadata.get('source', 'Unknown')
                print(f"   {i}. {source}")

            return True
        else:
            print("⚠️  ChromaDB collections appear to be empty")
            return False

    except Exception as e:
        print(f"❌ ChromaDB test failed: {str(e)}")
        return False

def test_data_manager_rag():
    """Test RAG through DataManager"""
    print("\n🔗 Testing RAG through DataManager")
    print("=" * 50)

    try:
        load_dotenv()
        from data_manager import DataManager

        data_manager = DataManager(
            open_router_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Test IT sector focused query
        query = "Indian IT sector performance analysis Q2 FY26 earnings trends"

        print(f"🔍 Testing query: {query}")

        # Use search function which should automatically include RAG
        results = data_manager.search(query)

        print("✅ DataManager RAG Integration Results:")
        print("-" * 30)

        if "RAG" in results:
            rag_data = results["RAG"]
            if rag_data and len(rag_data) > 0:
                print(f"   📝 RAG retrieved {len(rag_data)} chunks")
                # Show preview of first chunk
                first_chunk = rag_data[0][:200] + "..." if len(rag_data[0]) > 200 else rag_data[0]
                print(f"   📖 First chunk: {first_chunk}")

                # Save complete results
                with open('outputs/data_manager_rag_test.json', 'w') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

                print(f"   💾 Complete results saved to outputs/data_manager_rag_test.json")
                return True
            else:
                print("   ⚠️  RAG returned no data")
                return False
        else:
            print("   ❌ RAG not included in results")
            return False

    except Exception as e:
        print(f"❌ DataManager RAG test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting RAG Connector Tests")
    print("=" * 60)

    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)

    # Test 1: ChromaDB collections
    test1_result = test_chromadb_collections()

    # Test 2: Direct RAG connector
    test2_result = test_direct_rag_connector()

    # Test 3: DataManager integration
    test3_result = test_data_manager_rag()

    print("\n📋 Test Summary:")
    print("=" * 30)
    print(f"ChromaDB Collections: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Direct RAG Connector: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"DataManager Integration: {'✅ PASSED' if test3_result else '❌ FAILED'}")

    if test1_result and test2_result and test3_result:
        print("\n🎉 All RAG tests passed! RAG connector is working properly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some RAG tests failed. Check the error messages above.")
        sys.exit(1)