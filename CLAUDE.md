This project is managed using astral-uv (uv sync).

# Dialectical Agent System - 2 Ethos Personas

## Overview
This system implements a structured debate between two AI agents with opposing analytical approaches to the Indian IT/Technology sector:
- **Growth Believer**: Evidence-led optimist focusing on compounding dynamics
- **Cynic**: Motive-skeptic emphasizing downside risks and fragilities

## Key Features
- **Direct Agent-to-Agent Exchanges**: No broadcast model, only targeted responses
- **Structured Protocol**: Round 1 (Opening) → Round 2 (Targeted Rebuttals)
- **Evidence Requirements**: All claims must include source + date citations
- **Token Constraints**: ≤1000 tokens per turn, max 2 turns per agent
- **Confidence Scoring**: All assessments include confidence ∈ {0.1…0.9}

## Agent Ethos
### Growth Believer
- **Axiom**: "Compounding favors quality operators with reinvestment runways"
- **Method**: Growth engine mapping, moat diagnostics, bottleneck analysis
- **Focus**: TAM expansion, pricing power, operating leverage, structural growth

### Cynic
- **Axiom**: "Actors optimize self-interest; reported narratives conceal tradeoffs"
- **Method**: Incentive mapping, accounting analysis, fragility testing
- **Focus**: Management motivations, accounting quality, tail risk scenarios

## Technical Stack
- **Models**: DeepSeek R1 for agents, Qwen thinking for synthesis
- **Framework**: LangChain + LangGraph with direct agent routing
- **Domain**: Indian IT/Technology sector with temporal data emphasis
- **Reasoning**: Very high effort (high reasoning tokens) for detailed analysis
- **Meta-Analysis**: Comprehensive synthesis reports with NEE calculations and proper formatting

## Usage
```bash
uv sync
python main.py
```

Outputs include debate transcripts, raw data (JSON), and synthesis reports in markdown/PDF formats.