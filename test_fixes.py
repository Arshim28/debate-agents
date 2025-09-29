#!/usr/bin/env python3
"""
Test specific fixes for ethos loading and index names
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from agents import load_ethos_persona
from intelligent_data_loader import IntelligentFinancialDataLoader

def test_ethos_loading():
    """Test ethos persona loading"""
    print("=== Testing Ethos Persona Loading ===")

    try:
        print("1. Testing Growth Believer ethos...")
        growth_prompt = load_ethos_persona("growth_believer")
        print(f"✓ Growth Believer loaded: {len(growth_prompt)} characters")
        print(f"Preview: {growth_prompt[:200]}...")

        print("\n2. Testing Cynic ethos...")
        cynic_prompt = load_ethos_persona("cynic")
        print(f"✓ Cynic loaded: {len(cynic_prompt)} characters")
        print(f"Preview: {cynic_prompt[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Ethos loading failed: {e}")
        return False

def test_market_data():
    """Test market data with correct index names"""
    print("\n=== Testing Market Data Access ===")

    try:
        load_dotenv()

        print("1. Initializing data loader...")
        data_loader = IntelligentFinancialDataLoader()
        print("✓ Data loader initialized")

        print("2. Testing market data with correct index name...")
        market_data = data_loader.get_market_data_context(["Nifty IT"], "1m")
        print(f"✓ Market data retrieved: {len(market_data)} characters")
        print(f"Preview: {market_data[:300]}...")

        return True

    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_single_agent_query():
    """Test single agent query with all fixes"""
    print("\n=== Testing Single Agent Query (All Fixes) ===")

    try:
        from agents import DebateAgent
        from config import AgentConfig, ModelConfig

        print("1. Creating agent with fixed ethos...")
        model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=200,
            api_key_env="OPENROUTER_API_KEY"
        )

        agent_config = AgentConfig(
            name="Fixed Test Agent",
            role="Test",
            perspective="bullish",
            model=model_config,
            system_prompt="Test with fixed ethos",
            max_turns=1
        )

        data_loader = IntelligentFinancialDataLoader()
        agent = DebateAgent(agent_config, data_loader)
        print("✓ Agent created with fixes")

        print("2. Testing optimized query execution...")
        fresh_intelligence = agent._formulate_and_execute_queries(
            debate_context="Fixed test query for Indian IT sector",
            opponent_messages=None,
            turn_number=1
        )

        print(f"✓ Query completed: {len(fresh_intelligence)} characters")
        print("Query preview:")
        print("=" * 40)
        print(fresh_intelligence[:400] + "..." if len(fresh_intelligence) > 400 else fresh_intelligence)
        print("=" * 40)

        return True

    except Exception as e:
        print(f"❌ Single agent query failed: {e}")
        return False

def main():
    print("Testing System Fixes")
    print("=" * 50)

    results = []
    results.append(("Ethos Loading", test_ethos_loading()))
    results.append(("Market Data", test_market_data()))
    results.append(("Single Agent Query", test_single_agent_query()))

    print("\n" + "=" * 50)
    print("FIX TEST SUMMARY:")
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name}: {status}")

    total_pass = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_pass}/{len(results)} fixes verified")

    if total_pass == len(results):
        print("\n✅ All fixes working! System ready for debate.")
    else:
        print("\n⚠️  Some fixes still need work.")

if __name__ == "__main__":
    main()