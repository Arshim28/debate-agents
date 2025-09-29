from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
import os
from pathlib import Path

class ModelConfig(BaseModel):
    provider: Literal["openai", "anthropic", "openrouter"] = "openrouter"
    model_name: str = "openrouter/deepseek/deepseek-r1"  # Updated for reasoning model
    temperature: float = 0.3  # Lower temperature for reasoning models
    max_tokens: int = 2000  # Doubled token limit for detailed analysis
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url: Optional[str] = "https://openrouter.ai/api/v1"
    # Reasoning effort controls for OpenRouter
    reasoning_effort: Optional[str] = "high"  # low, medium, high
    max_reasoning_tokens: Optional[int] = 15000  # Control reasoning depth

class AgentConfig(BaseModel):
    name: str
    role: str
    perspective: Literal["bull", "bear", "neutral", "analytical", "defensive", "systematic", "balanced", "bullish", "bearish", "contrarian", "opportunistic"]
    model: ModelConfig
    system_prompt: str
    max_turns: int = 5

class DebateConfig(BaseModel):
    topic: str = "Indian IT/Technology Sector Analysis - September 2025"
    max_debate_turns: int = 2  # Reduced to 2 turns per agent max
    max_rounds: int = 2  # Maximum debate rounds
    output_directory: str = "outputs"
    reasoning_depth: int = 3  # Advanced reasoning depth for reasoning models

class SystemConfig(BaseModel):
    # Legacy fields for backwards compatibility (not used in advanced system)
    bull_agent: Optional[AgentConfig] = None
    bear_agent: Optional[AgentConfig] = None
    orchestrator: ModelConfig
    synthesis_agent: ModelConfig
    debate: DebateConfig

    @classmethod
    def create_default(cls) -> "SystemConfig":
        base_model = ModelConfig(
            model_name="x-ai/grok-4-fast:free",  # Grok model for agents
            temperature=0.3,
            max_tokens=2000,  # Doubled from 1000 for detailed analysis
            api_key_env="OPENROUTER_API_KEY",
            reasoning_effort="high",  # Very high reasoning for agents
            max_reasoning_tokens=15000
        )

        return cls(
            # Legacy agents set to None - we use optimized personas instead
            bull_agent=None,
            bear_agent=None,
            orchestrator=base_model,
            synthesis_agent=ModelConfig(
                model_name="qwen/qwen3-next-80b-a3b-thinking",  # Qwen thinking model for meta-analysis
                temperature=0.2,  # Even lower for meta-analysis
                max_tokens=16000,  # Increased for comprehensive reports
                api_key_env="OPENROUTER_API_KEY",
                reasoning_effort="high",  # High reasoning for meta-analysis
                max_reasoning_tokens=20000
            ),
            debate=DebateConfig()
        )

def load_config() -> SystemConfig:
    config_file = Path("config.json")
    if config_file.exists():
        import json
        with open(config_file, 'r') as f:
            data = json.load(f)
        return SystemConfig(**data)
    else:
        return SystemConfig.create_default()

def save_config(config: SystemConfig):
    import json
    with open("config.json", 'w') as f:
        json.dump(config.model_dump(), f, indent=2)

def get_llm_from_config(model_config: ModelConfig):
    if model_config.provider == "openrouter":
        from langchain_openai import ChatOpenAI
        # Use API key from environment variable
        api_key = os.getenv(model_config.api_key_env)

        # Configure reasoning effort via OpenRouter headers
        extra_headers = {}
        if model_config.reasoning_effort:
            extra_headers["x-reasoning-effort"] = model_config.reasoning_effort
        if model_config.max_reasoning_tokens:
            extra_headers["x-max-reasoning-tokens"] = str(model_config.max_reasoning_tokens)

        return ChatOpenAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=api_key,
            base_url=model_config.base_url,
            default_headers=extra_headers
        )
    elif model_config.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=os.getenv(model_config.api_key_env)
        )
    elif model_config.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=os.getenv(model_config.api_key_env)
        )
    else:
        raise ValueError(f"Unsupported provider: {model_config.provider}")