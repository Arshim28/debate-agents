#!/usr/bin/env python3
"""
Test script to verify all data connectors work properly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from data_manager import DataManager
from connectors.indices_tracker import NiftyIndicesTracker
from connectors.youtube_connector import YouTubeConnector
from connectors.jina_web_connector import JinaSearchTool
from connectors.local_docs_connector import DataRetriever

def test_indices_tracker():
    """Test Nifty indices tracking"""
    print("=== Testing Nifty Indices Tracker ===")
    try:
        tracker = NiftyIndicesTracker()

        # Test getting index list
        indices = tracker.list_indices()
        print(f"Available indices: {len(indices)} total")
        print(f"Sample indices: {indices[:5]}")

        # Test getting data
        result = tracker.get_data("Nifty IT", "01-Sep-2024", "01-Oct-2024", "weekly")
        print(f"Nifty IT sample data: {list(result.items())[:3]}")

        print("✓ Indices tracker working\n")
        return True
    except Exception as e:
        print(f"✗ Indices tracker failed: {e}\n")
        return False

def test_youtube_connector():
    """Test YouTube connector"""
    print("=== Testing YouTube Connector ===")
    try:
        load_dotenv()
        connector = YouTubeConnector(api_key=os.getenv("YOUTUBE_API_KEY"))

        # Test video search
        videos = connector.video_search("Indian IT sector AI impact", max_results=3)
        print(f"Found {len(videos)} videos")
        if videos:
            print(f"Sample video: {videos[0]['title']}")

            # Test transcript (just try first video)
            transcript = connector.get_transcript(videos[0]['video_id'])
            if isinstance(transcript, str) and len(transcript) > 100:
                print(f"Transcript preview: {transcript[:200]}...")
                print("✓ YouTube connector working\n")
                return True
            else:
                print(f"Transcript issue: {transcript}")

        print("✓ YouTube search working (transcript may vary)\n")
        return True
    except Exception as e:
        print(f"✗ YouTube connector failed: {e}\n")
        return False

def test_jina_connector():
    """Test Jina web search"""
    print("=== Testing Jina Web Connector ===")
    try:
        load_dotenv()
        connector = JinaSearchTool(api_key=os.getenv("JINA_API_KEY"))

        # Test web search
        results = connector.search("Indian IT sector Q1 2025 results")
        print(f"Found {len(results)} search results")
        if results:
            print(f"Sample result: {results[0]['title']}")
            print(f"Sample content: {results[0]['content'][:200]}...")

        print("✓ Jina web search working\n")
        return True
    except Exception as e:
        print(f"✗ Jina web search failed: {e}\n")
        return False

def test_local_rag():
    """Test local RAG retrieval"""
    print("=== Testing Local RAG Retrieval ===")
    try:
        load_dotenv()
        retriever = DataRetriever(
            summary_collection_name="document_summary",
            chunk_collection_name="document_chunks",
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Test retrieval
        chunks = retriever.retrieve("What is the outlook for Indian IT sector after AI boom?")
        print(f"Retrieved {len(chunks)} relevant chunks")
        if chunks:
            print(f"Sample chunk: {chunks[0][:200]}...")

        print("✓ Local RAG retrieval working\n")
        return True
    except Exception as e:
        print(f"✗ Local RAG retrieval failed: {e}\n")
        return False

def test_data_manager():
    """Test integrated data manager"""
    print("=== Testing Integrated Data Manager ===")
    try:
        load_dotenv()
        dm = DataManager(
            open_router_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            summary_collection_name="document_summary",
            chunk_collection_name="document_chunks"
        )

        # Test intelligent search
        query = "What is the current state of Indian IT sector and impact of AI?"
        print(f"Testing query: {query}")

        result = dm.search(query)
        print(f"Data sources found: {list(result.keys())}")

        # Show samples from each source
        for source, data in result.items():
            if isinstance(data, dict) and data:
                print(f"  {source}: {len(data)} items")
            elif isinstance(data, list) and data:
                print(f"  {source}: {len(data)} items")
                if source == "RAG":
                    print(f"    Sample: {data[0][:100]}...")

        print("✓ Data manager integration working\n")
        return True
    except Exception as e:
        print(f"✗ Data manager failed: {e}\n")
        return False

def main():
    print("Testing All Data Connectors\n")
    print("=" * 50)

    results = []
    results.append(("Indices Tracker", test_indices_tracker()))
    results.append(("YouTube Connector", test_youtube_connector()))
    results.append(("Jina Web Search", test_jina_connector()))
    results.append(("Local RAG", test_local_rag()))
    results.append(("Data Manager", test_data_manager()))

    print("=" * 50)
    print("SUMMARY:")
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name}: {status}")

    total_pass = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_pass}/{len(results)} connectors working")

if __name__ == "__main__":
    main()