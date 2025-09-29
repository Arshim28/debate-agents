#!/usr/bin/env python3
"""
Debug script to identify query execution bottlenecks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from dotenv import load_dotenv
from intelligent_data_loader import IntelligentFinancialDataLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_loader_queries():
    """Test individual data loader methods to identify bottlenecks"""
    print("=== Debug: Data Loader Query Performance ===")

    try:
        load_dotenv()

        print("1. Initializing data loader...")
        data_loader = IntelligentFinancialDataLoader()
        print("✓ Data loader initialized")

        print("\n2. Testing basic context retrieval...")
        try:
            context = data_loader.get_financial_context()
            print(f"✓ Basic context retrieved: {len(context)} chars")
        except Exception as e:
            print(f"❌ Basic context failed: {e}")

        print("\n3. Testing intelligent context with simple query...")
        try:
            simple_query = "TCS latest results"
            intelligent_context = data_loader.get_intelligent_context(simple_query)
            print(f"✓ Intelligent context retrieved: {len(intelligent_context)} chars")
        except Exception as e:
            print(f"❌ Intelligent context failed: {e}")

        print("\n4. Testing document search...")
        try:
            docs = data_loader.search_documents("TCS financial performance", max_results=2)
            print(f"✓ Document search completed: {len(docs)} results")
        except Exception as e:
            print(f"❌ Document search failed: {e}")

        print("\n5. Testing market data context...")
        try:
            market_data = data_loader.get_market_data_context(["Nifty IT"], "1m")
            print(f"✓ Market data retrieved: {len(market_data)} chars")
        except Exception as e:
            print(f"❌ Market data failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Data loader test failed: {e}")
        return False

def test_agent_query_method():
    """Test the agent query method in isolation"""
    print("\n=== Debug: Agent Query Method ===")

    try:
        from agents import DebateAgent
        from config import AgentConfig, ModelConfig

        # Create minimal agent config for testing
        model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=100,  # Very small for testing
            api_key_env="OPENROUTER_API_KEY"
        )

        agent_config = AgentConfig(
            name="Debug Agent",
            role="Debug",
            perspective="bullish",
            model=model_config,
            system_prompt="Debug agent",
            max_turns=1
        )

        print("1. Creating debug agent...")
        data_loader = IntelligentFinancialDataLoader()
        agent = DebateAgent(agent_config, data_loader)
        print("✓ Debug agent created")

        print("\n2. Testing query execution method...")
        try:
            test_context = "Simple test query"

            # This is where it might be hanging
            logger.info("Starting query execution test...")
            fresh_intelligence = agent._formulate_and_execute_queries(
                debate_context=test_context,
                opponent_messages=None,
                turn_number=1
            )
            print(f"✓ Query execution completed: {len(fresh_intelligence)} chars")
            print(f"Preview: {fresh_intelligence[:200]}...")

        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            logger.error(f"Query execution error: {e}")

        return True

    except Exception as e:
        print(f"❌ Agent query test failed: {e}")
        return False

def main():
    print("Debugging Query-Driven System Bottlenecks")
    print("=" * 60)

    # Test data loader first
    dl_success = test_data_loader_queries()

    if dl_success:
        # Test agent queries if data loader works
        agent_success = test_agent_query_method()

        if agent_success:
            print("\n✅ All debug tests passed - issue is elsewhere")
        else:
            print("\n❌ Agent query method has issues")
    else:
        print("\n❌ Data loader has fundamental issues")

if __name__ == "__main__":
    main()