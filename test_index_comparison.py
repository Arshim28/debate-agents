#!/usr/bin/env python3
"""
Test script for Index Comparison functionality
Tests Nifty 50 vs Nifty IT comparison across multiple timeframes
"""

import sys
import os
from dotenv import load_dotenv
from connectors.indices_tracker import NiftyIndicesTracker
import json

def test_index_comparison():
    """Test the compare_indices functionality"""
    print("🔍 Testing Nifty 50 vs Nifty IT Comparison")
    print("=" * 50)

    # Initialize tracker
    tracker = NiftyIndicesTracker()

    # Test comparison across multiple timeframes
    timeframes = ['1w', '1m', '3m', '6m', '1y']

    try:
        results = tracker.compare_indices(
            index1="Nifty 50",
            index2="Nifty IT",
            timeframes=timeframes
        )

        print("✅ Comparison Results:")
        print("-" * 30)

        for timeframe, data in results.items():
            print(f"\n📊 {timeframe.upper()} Performance:")
            if 'error' in data:
                print(f"   ❌ Error: {data['error']}")
            else:
                print(f"   📅 Period: {data['start_date']} to {data['end_date']}")
                print(f"   📈 Nifty 50 Return: {data.get('Nifty 50_return', 'N/A')}%")
                print(f"   💻 Nifty IT Return: {data.get('Nifty IT_return', 'N/A')}%")
                print(f"   🎯 Outperformance: {data.get('outperformance', 'N/A')}%")
                print(f"   📊 Data Points: {data.get('data_points', 'N/A')}")

        # Save results for analysis
        with open('outputs/index_comparison_test.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to outputs/index_comparison_test.json")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_data_manager_integration():
    """Test integration with DataManager"""
    print("\n🔗 Testing DataManager Integration")
    print("=" * 50)

    load_dotenv()

    try:
        from data_manager import DataManager

        data_manager = DataManager(
            open_router_api_key=os.getenv("OPEN_ROUTER_API_KEY"),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            jina_api_key=os.getenv("JINA_API_KEY"),
            gemini_api_key=os.getenv("GEMINI_API_KEY")
        )

        # Test query that should trigger index comparison
        query = "Compare Nifty IT vs Nifty 50 performance across different timeframes"

        print(f"🔍 Testing query: {query}")

        # Manual tool selection for testing
        tools_config = {
            "Index Comparison": {
                "tool_args": {
                    "index1": "Nifty 50",
                    "index2": "Nifty IT",
                    "timeframes": ["1w", "1m", "3m", "6m"]
                }
            }
        }

        results = data_manager.search(query, tools=json.dumps(tools_config))

        print("✅ DataManager Integration Results:")
        print("-" * 30)

        for tool_name, data in results.items():
            print(f"\n📊 {tool_name}:")
            if isinstance(data, dict) and len(data) > 0:
                print(f"   ✓ Retrieved {len(data)} items")
                if tool_name == "Index Comparison":
                    for timeframe, metrics in data.items():
                        if 'error' not in metrics:
                            print(f"   📈 {timeframe}: {metrics.get('outperformance', 'N/A')}% outperformance")
            else:
                print(f"   ⚠️  No data retrieved")

        return True

    except Exception as e:
        print(f"❌ DataManager test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Index Comparison Tests")
    print("=" * 60)

    # Test 1: Direct tracker functionality
    test1_result = test_index_comparison()

    # Test 2: DataManager integration
    test2_result = test_data_manager_integration()

    print("\n📋 Test Summary:")
    print("=" * 30)
    print(f"Direct Tracker Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"DataManager Integration: {'✅ PASSED' if test2_result else '❌ FAILED'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! Index comparison functionality is ready.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1)