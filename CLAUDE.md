This project is managed using astral-uv (uv sync).

# Dialectical Agent System - 2 Ethos Personas with Dynamic Sector Intelligence

## Overview
This system implements a structured debate between two AI agents with opposing analytical approaches to the Indian IT/Technology sector:
- **Growth Believer**: Evidence-led optimist focusing on compounding dynamics and structural opportunities
- **Cynic**: Motive-skeptic emphasizing downside risks, regulatory challenges, and structural headwinds

**🎯 MISSION CRITICAL**: Agents dynamically generate exactly 3 sector-focused queries per round with temporal awareness, adapting to debate context for data-driven sectoral analysis.

## Key Features
- **Dynamic Query Generation**: LLM-powered sector-level query formulation (exactly 3 per agent per round)
- **Temporal Intelligence**: Automatic financial year/quarter detection using Python datetime
- **Sector-Focused Analysis**: Emphasis on policies, macroeconomic trends, and industry transformation (not individual companies)
- **Graceful Error Handling**: Continues execution on data failures without fabricating information
- **Query-Driven Responses**: Mandatory 2-phase workflow (data gathering → informed response)
- **Direct Agent-to-Agent Exchanges**: No broadcast model, only targeted responses
- **Structured Protocol**: Round 1 (Opening) → Round 2 (Targeted Rebuttals)
- **Fresh Data Enforcement**: Zero tolerance for training data usage
- **Evidence Requirements**: All claims must include specific dates and sources from live data
- **Token Constraints**: ≤2000 tokens per turn, max 2 turns per agent
- **Adaptive Intelligence**: Context-aware queries that respond to opponent arguments

## Agent Ethos
### Growth Believer
- **Axiom**: "Compounding favors quality operators with reinvestment runways"
- **Method**: Growth engine mapping, moat diagnostics, bottleneck analysis
- **Focus**: Government digital policies, AI transformation opportunities, global outsourcing trends
- **Query Strategy**: Dynamic generation targeting policy support, technological adoption, competitive advantages

### Cynic
- **Axiom**: "Actors optimize self-interest; reported narratives conceal tradeoffs"
- **Method**: Incentive mapping, regulatory analysis, fragility testing
- **Focus**: Regulatory challenges, automation threats, macroeconomic headwinds
- **Query Strategy**: Dynamic generation targeting compliance costs, job displacement, structural disruptions

## Technical Stack
- **Models**: Grok-4-Fast for agents (high reasoning effort), Qwen for synthesis
- **Framework**: LangChain + LangGraph with advanced orchestration
- **Domain**: Indian IT/Technology sector with dynamic temporal awareness
- **Query Architecture**: 3-query deterministic workflow with graceful error handling
- **Date System**: Python datetime-based FY/quarter auto-detection (`date_utils.py`)
- **Meta-Analysis**: Comprehensive synthesis reports with dialectical resolution

## Query-Driven Data Infrastructure
### **Mandatory 2-Phase Response Workflow**
1. **Phase 1 - Sector Data Gathering**: Agent executes exactly 3 targeted sector-level queries
2. **Phase 2 - Informed Response**: Agent uses only fresh data to formulate arguments

### **Multi-Modal Data Connectors (Priority Order)**
- **ChromaDB RAG System**: 11 proprietary research documents, 169 chunks (HIGHEST PRIORITY)
- **Jina Web Search**: Live web search with India-focused market intelligence
- **YouTube Connector**: Automated transcript extraction from analyst interviews
- **Nifty Indices Tracker**: Real-time access to 143+ Indian market indices (with timeout handling)
- **Gemini Embeddings**: Semantic search capabilities for document retrieval

### **Dynamic Query Features**
- **Temporal Intelligence**: Automatic FY26/Q2 detection with `get_current_financial_context()`
- **Sector-Level Focus**: Government policies, regulatory changes, macroeconomic trends
- **Perspective-Specific Targeting**: Bullish seeks opportunities, bearish seeks challenges
- **Error Resilience**: Continues execution on connector failures without fabricating data
- **Throttled Execution**: 2-second delays between API calls to prevent rate limiting
- **Multi-Source Synthesis**: Combines RAG, web search, market data, and video transcripts

## Data Manager Integration
- **Intelligent Routing**: LLM-based query routing with RAG prioritization
- **Fresh Intelligence Compilation**: Real-time market data with timestamp verification
- **Context-Aware Search**: Filters and ranks information relevance for debate consumption
- **Source Validation**: Ensures all claims include specific dates and data sources
- **Error Transparency**: Clear indication when data sources fail without system crashes

## Usage
```bash
uv sync
python main.py
```

**Expected Execution**:
- 4 agent responses (2 per agent)
- Each response preceded by exactly 3 sector-focused queries with current FY26/Q2 context
- Complete debate with multi-source intelligence emphasizing sector-level analysis
- Meta-analysis synthesis with dialectical resolution
- Outputs: Transcripts, raw data (JSON), synthesis reports (markdown/PDF)

**Current Context**: System automatically detects Q2 FY26 (July-September 2025) and generates sector-focused queries about policies, regulations, and industry transformation.

**Query Examples**:
- Bullish: "Indian IT sector government digital initiatives Q2 FY26 infrastructure investment"
- Bearish: "Indian IT sector regulatory challenges compliance costs Q2 FY26 policy uncertainty"

**Verification**: Check logs for "completed X/3 queries successfully" confirmations and sector-level query focus.
- Never use the word "enhanced" either as prefix, suffix, file name, classname or function name in my codebases.