#!/usr/bin/env python3
"""
CLI tool to test reasoning capabilities with different models via OpenRouter API
"""
import os
import sys
import argparse
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_api_key() -> str:
    """Get API key from environment or config"""
    # Try to get from environment first
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    # Try to get from the same key used in config.py
    hardcoded_key = "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"
    return hardcoded_key

def test_reasoning_model(
    model_name: str,
    reasoning_effort: Optional[str] = None,
    max_reasoning_tokens: Optional[int] = None,
    temperature: float = 0.3,
    max_tokens: int = 800,
    verbose: bool = False
):
    """Test reasoning capabilities with specified model"""

    logger = logging.getLogger(__name__)

    try:
        # Get API key
        api_key = get_api_key()
        if not api_key:
            raise ValueError("No OpenRouter API key found. Set OPENROUTER_API_KEY environment variable.")

        print(f"🧪 Testing Reasoning with Model: {model_name}")
        print("=" * 60)

        # Configure model with reasoning parameters via headers only
        extra_headers = {}

        if reasoning_effort:
            extra_headers["x-reasoning-effort"] = reasoning_effort
            print(f"🧠 Reasoning Effort: {reasoning_effort}")

        if max_reasoning_tokens:
            extra_headers["x-max-reasoning-tokens"] = str(max_reasoning_tokens)
            print(f"🎯 Max Reasoning Tokens: {max_reasoning_tokens}")

        print(f"🌡️  Temperature: {temperature}")
        print(f"📝 Max Output Tokens: {max_tokens}")
        print()

        if verbose:
            print(f"🔧 Extra Headers: {extra_headers}")
            print()

        # Initialize the model
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers=extra_headers
        )

        # Test reasoning with a complex problem
        test_prompt = """
        You are analyzing the Indian IT/Technology sector. Please provide a detailed analysis that requires step-by-step reasoning:

        Problem: A major Indian IT services company is considering whether to invest heavily in AI/ML capabilities versus expanding their traditional software development services. They have the following constraints:

        1. Budget: $100M to allocate
        2. Current revenue split: 70% traditional services, 30% emerging tech
        3. Market trends: AI/ML demand growing 40% YoY, traditional services growing 8% YoY
        4. Competition: 3 major competitors already investing heavily in AI/ML
        5. Talent: Need to retrain 2000 engineers or hire 500 new AI specialists

        Please reason through this decision step-by-step, considering:
        - ROI analysis for both options
        - Risk assessment
        - Market positioning implications
        - Implementation timeline and challenges

        Provide a clear recommendation with your reasoning process.
        """

        print("🤔 Test Prompt: Complex IT Sector Investment Decision")
        print("-" * 50)

        # Make the API call
        print("⏳ Generating response with reasoning...")
        response = llm.invoke([HumanMessage(content=test_prompt)])

        print("✅ Response Generated Successfully!")
        print("=" * 60)
        print("🤖 AI Response:")
        print("-" * 20)
        print(response.content)
        print()
        print("=" * 60)

        # Check if response shows reasoning patterns
        response_text = response.content.lower()
        reasoning_indicators = [
            "step-by-step", "first", "second", "next", "then", "therefore",
            "analysis", "considering", "given that", "we can see", "conclusion"
        ]

        found_indicators = [ind for ind in reasoning_indicators if ind in response_text]

        print("🔍 Reasoning Analysis:")
        print(f"📏 Response Length: {len(response.content)} characters")
        print(f"🧩 Reasoning Indicators Found: {len(found_indicators)}")
        if found_indicators:
            print(f"   Indicators: {', '.join(found_indicators[:5])}")

        # Check for structured reasoning
        if any(marker in response_text for marker in ["1.", "2.", "3.", "step 1", "step 2"]):
            print("✅ Structured reasoning detected")
        else:
            print("⚠️  No clear structured reasoning detected")

        return True

    except Exception as e:
        logger.error(f"Error testing reasoning model: {e}")
        print(f"❌ Error: {e}")
        return False

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Test reasoning capabilities with OpenRouter models")

    parser.add_argument(
        "--model",
        default="x-ai/grok-4-fast:free",
        help="Model name to test (default: x-ai/grok-4-fast:free)"
    )

    parser.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default="medium",
        help="Reasoning effort level (default: medium)"
    )

    parser.add_argument(
        "--max-reasoning-tokens",
        type=int,
        default=10000,
        help="Maximum reasoning tokens (default: 10000)"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Temperature for generation (default: 0.3)"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Maximum output tokens (default: 800)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Test without reasoning parameters"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    print("🧪 OpenRouter Reasoning Test CLI")
    print("=" * 40)

    # Set reasoning parameters
    reasoning_effort = None if args.no_reasoning else args.reasoning_effort
    max_reasoning_tokens = None if args.no_reasoning else args.max_reasoning_tokens

    success = test_reasoning_model(
        model_name=args.model,
        reasoning_effort=reasoning_effort,
        max_reasoning_tokens=max_reasoning_tokens,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        verbose=args.verbose
    )

    if success:
        print("🎉 Reasoning test completed successfully!")
        sys.exit(0)
    else:
        print("💥 Reasoning test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()