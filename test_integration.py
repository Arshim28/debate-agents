#!/usr/bin/env python3
"""
Test script to verify the intelligent data loader integration with agents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from intelligent_data_loader import IntelligentFinancialDataLoader
from config import AgentConfig, ModelConfig

def test_intelligent_data_loader():
    """Test the intelligent data loader functionality"""
    print("=== Testing Intelligent Data Loader ===")

    try:
        # Initialize the data loader
        loader = IntelligentFinancialDataLoader()

        print("✓ Data loader initialized successfully")

        # Test getting financial context
        print("Fetching financial context...")
        context = loader.get_financial_context()

        print(f"Context length: {len(context)} characters")
        print("Context preview:")
        print("=" * 50)
        print(context[:500] + "...")
        print("=" * 50)

        # Test document search
        print("\nTesting document search...")
        results = loader.search_documents("AI impact on Indian IT sector", max_results=3)
        print(f"Found {len(results)} relevant chunks")
        if results:
            print(f"Sample result: {results[0][:200]}...")

        # Test market data context
        print("\nTesting market data context...")
        market_context = loader.get_market_data_context(["Nifty IT"], "1m")
        print(f"Market context preview: {market_context[:300]}...")

        print("\n✓ All intelligent data loader tests passed")
        return True

    except Exception as e:
        print(f"✗ Intelligent data loader test failed: {e}")
        return False

def test_agent_integration():
    """Test that agents can use the new data loader"""
    print("\n=== Testing Agent Integration ===")

    try:
        from agents import DebateAgent

        # Create a test agent config
        model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=500,
            api_key_env="OPENROUTER_API_KEY"
        )

        agent_config = AgentConfig(
            name="Test Agent",
            role="Test Analyst",
            perspective="bullish",
            model=model_config,
            system_prompt="You are a test financial analyst.",
            max_turns=1
        )

        # Initialize data loader
        data_loader = IntelligentFinancialDataLoader()

        # Create agent
        agent = DebateAgent(agent_config, data_loader)

        print("✓ Agent created with intelligent data loader")

        # Test that agent can access data context
        context = agent.data_loader.get_financial_context()
        print(f"Agent can access context: {len(context)} characters")

        print("✓ Agent integration test passed")
        return True

    except Exception as e:
        print(f"✗ Agent integration test failed: {e}")
        return False

def main():
    print("Testing Intelligent Data Integration")
    print("=" * 50)

    load_dotenv()

    results = []
    results.append(("Intelligent Data Loader", test_intelligent_data_loader()))
    results.append(("Agent Integration", test_agent_integration()))

    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY:")
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name}: {status}")

    total_pass = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_pass}/{len(results)} tests passed")

    if total_pass == len(results):
        print("\n🎉 All integration tests passed! System is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()