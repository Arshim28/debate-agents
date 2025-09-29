#!/usr/bin/env python3
"""
Test script to verify the new query-driven agent workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from agents import DebateAgent
from intelligent_data_loader import IntelligentFinancialDataLoader
from config import AgentConfig, ModelConfig

def test_query_execution():
    """Test the new query-driven workflow"""
    print("=== Testing Query-Driven Agent Workflow ===")

    try:
        load_dotenv()

        # Create test agent with minimal config
        model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=200,  # Small for testing
            api_key_env="OPENROUTER_API_KEY"
        )

        agent_config = AgentConfig(
            name="Test Growth Believer",
            role="Test Analyst",
            perspective="bullish",
            model=model_config,
            system_prompt="You are a test analyst focused on Indian IT sector.",
            max_turns=2
        )

        # Initialize components
        data_loader = IntelligentFinancialDataLoader()
        agent = DebateAgent(agent_config, data_loader)

        print("✓ Agent initialized with query-driven workflow")

        # Test the query execution method directly
        print("\nTesting query execution method...")
        test_context = "Current state of Indian IT sector growth prospects and challenges"

        fresh_intelligence = agent._formulate_and_execute_queries(
            debate_context=test_context,
            opponent_messages=None,
            turn_number=1
        )

        print(f"✓ Query execution completed")
        print(f"Fresh intelligence length: {len(fresh_intelligence)} characters")
        print("\nFresh intelligence preview:")
        print("=" * 60)
        print(fresh_intelligence[:500] + "..." if len(fresh_intelligence) > 500 else fresh_intelligence)
        print("=" * 60)

        # Verify query structure
        if "FRESH MARKET INTELLIGENCE" in fresh_intelligence:
            print("✓ Fresh intelligence format correct")
        else:
            print("❌ Fresh intelligence format incorrect")

        if "Query Execution Time:" in fresh_intelligence:
            print("✓ Timestamp included in fresh data")
        else:
            print("❌ Timestamp missing from fresh data")

        print("\n✅ Query-driven workflow test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Query workflow test failed: {e}")
        return False

def main():
    print("Testing Query-Driven Agent System")
    print("=" * 50)

    success = test_query_execution()

    if success:
        print("\n🎉 Query-driven system is ready!")
        print("Agents will now actively query data connectors before each response.")
    else:
        print("\n⚠️  Query-driven system needs debugging.")

if __name__ == "__main__":
    main()