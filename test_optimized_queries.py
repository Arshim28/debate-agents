#!/usr/bin/env python3
"""
Test the optimized query-driven workflow with throttling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from dotenv import load_dotenv
from agents import DebateAgent
from intelligent_data_loader import IntelligentFinancialDataLoader
from config import AgentConfig, ModelConfig

def test_optimized_agent_queries():
    """Test optimized agent query workflow"""
    print("=== Testing Optimized Query Workflow ===")

    try:
        load_dotenv()

        # Create optimized test agent
        model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=300,  # Moderate size for testing
            api_key_env="OPENROUTER_API_KEY"
        )

        agent_config = AgentConfig(
            name="Optimized Test Agent",
            role="Test Analyst",
            perspective="bullish",
            model=model_config,
            system_prompt="You are an optimized test analyst.",
            max_turns=2
        )

        print("1. Creating optimized agent...")
        data_loader = IntelligentFinancialDataLoader()
        agent = DebateAgent(agent_config, data_loader)
        print("✓ Optimized agent created")

        print("\n2. Testing optimized query execution...")
        start_time = time.time()

        fresh_intelligence = agent._formulate_and_execute_queries(
            debate_context="Test optimized query system for Indian IT sector",
            opponent_messages=None,
            turn_number=1
        )

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"✓ Optimized query completed in {execution_time:.2f} seconds")
        print(f"Fresh intelligence length: {len(fresh_intelligence)} characters")

        # Check if we got valid data
        if "FRESH MARKET INTELLIGENCE" in fresh_intelligence:
            print("✓ Fresh intelligence format correct")
        else:
            print("❌ Fresh intelligence format incorrect")

        if "TARGETED QUERY" in fresh_intelligence:
            print("✓ Targeted query approach working")
        else:
            print("❌ Targeted query approach failed")

        # Show preview
        print("\nOptimized intelligence preview:")
        print("=" * 50)
        print(fresh_intelligence[:400] + "..." if len(fresh_intelligence) > 400 else fresh_intelligence)
        print("=" * 50)

        return True

    except Exception as e:
        print(f"❌ Optimized query test failed: {e}")
        return False

def test_simple_debate_round():
    """Test a simple single-turn debate with optimized queries"""
    print("\n=== Testing Simple Debate Round ===")

    try:
        from advanced_orchestrator import AdvancedDebateOrchestrator
        from config import load_config

        print("1. Loading config and creating orchestrator...")
        config = load_config()
        orchestrator = AdvancedDebateOrchestrator(config)
        print("✓ Orchestrator created")

        print("\n2. Testing single debate round...")
        start_time = time.time()

        # Get just the debate system for direct testing
        debate_messages = orchestrator.debate_system.run_debate_round(
            topic="Quick test of Indian IT sector outlook",
            max_rounds=1
        )

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"✓ Single debate round completed in {execution_time:.2f} seconds")
        print(f"Generated {len(debate_messages)} messages")

        # Show message previews
        for i, msg in enumerate(debate_messages, 1):
            print(f"\nMessage {i} ({msg.agent_name}):")
            print(f"Preview: {msg.content[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Simple debate round failed: {e}")
        return False

def main():
    print("Testing Optimized Query-Driven System")
    print("=" * 60)

    # Test optimized queries first
    query_success = test_optimized_agent_queries()

    if query_success:
        print("\n" + "=" * 40)
        # Test simple debate round if queries work
        debate_success = test_simple_debate_round()

        if debate_success:
            print("\n✅ All optimized tests passed!")
            print("System is ready for full debate execution.")
        else:
            print("\n⚠️  Query optimization worked, but debate round failed.")
    else:
        print("\n❌ Query optimization still has issues.")

if __name__ == "__main__":
    main()