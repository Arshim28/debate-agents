from typing import Dict, Any, List, Optional
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
import logging
from pathlib import Path

from config import AgentConfig, get_llm_from_config
from data_loader import FinancialDataLoader

logger = logging.getLogger(__name__)

class DebateMessage(BaseModel):
    agent_name: str
    perspective: str
    content: str
    turn_number: int
    timestamp: str = Field(default_factory=lambda: str(__import__('datetime').datetime.now()))

class DebateAgent:
    def __init__(self, config: AgentConfig, data_loader: FinancialDataLoader):
        self.config = config
        self.data_loader = data_loader
        self.llm = get_llm_from_config(config.model)
        self.conversation_history: List[DebateMessage] = []
        self.turn_count = 0
        self.max_turns_per_agent = 2  # New constraint: only 2 turns per agent

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._build_system_prompt()),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])

        # Create the chain
        self.chain = self.prompt | self.llm

    def _build_system_prompt(self) -> str:
        financial_context = self.data_loader.get_financial_context()

        return f"""{self.config.system_prompt}

AVAILABLE FINANCIAL DATA:
{financial_context}

DEBATE INSTRUCTIONS - IT/TECHNOLOGY SECTOR FOCUS WITH TEMPORAL EMPHASIS:
- You are participating in a structured multi-agent debate forum about the Indian IT/Technology sector
- SECTOR FOCUS: Keep ALL discussions centered on IT/Technology companies, trends, and market dynamics
- TEMPORAL FOCUS (CRITICAL):
  * PRIORITIZE RECENT DATA: Always lead with the most recent financial results, quarterly reports, and market developments
  * DATE SPECIFICITY: Reference exact time periods, quarters (Q1/Q2/Q3/Q4 FY25), months, and recent events
  * RECENCY WEIGHTING: Give higher analytical weight to latest data vs. older historical information
  * TREND ANALYSIS: Emphasize quarter-over-quarter (QoQ), year-over-year (YoY) changes and recent trajectories
  * CURRENT RELEVANCE: Frame all arguments within the current market context and recent industry shifts
- This is a reasoning-heavy environment - think step by step before presenting conclusions
- Present your arguments clearly with supporting evidence from the provided data
- Directly address and counter opposing viewpoints when they are presented
- Maintain your {self.config.perspective.upper()} perspective throughout the debate
- Use specific metrics, figures, and examples from the IT/Tech financial documents
- CRITICAL CONSTRAINTS:
  * Keep responses detailed but focused (MAX 2000 tokens per response)
  * You have EXACTLY 2 turns in this debate - use them strategically
- Focus on IT/Tech sector themes: digital transformation, AI/ML adoption, cloud migration, talent costs, client spending, regulatory impacts, etc.
- Format your response as a clear argument with supporting evidence, always emphasizing RECENT developments

Remember: This is an intellectual debate about IT/Technology sector - be respectful but firm in your position."""

    def respond(self, debate_context: str, opponent_messages: Optional[List[str]] = None, turn_number: int = 1) -> DebateMessage:
        history_messages = []

        # Add conversation history
        for msg in self.conversation_history[-4:]:  # Keep last 4 messages for context
            if msg.agent_name == self.config.name:
                history_messages.append(AIMessage(content=msg.content))
            else:
                history_messages.append(HumanMessage(content=f"[{msg.agent_name}]: {msg.content}"))

        # Build input message
        input_parts = [f"DEBATE CONTEXT: {debate_context}"]

        if opponent_messages:
            input_parts.append(f"\nOTHER PARTICIPANTS' ARGUMENTS:")
            for i, msg in enumerate(opponent_messages[-3:], 1):  # Only last 3 messages for context
                input_parts.append(f"\n{i}. {msg}")
            input_parts.append(f"\nTURN {self.turn_count + 1} OF 2: Respond to the above arguments while maintaining your {self.config.perspective.upper()} perspective on the Indian IT/Technology sector:")
        else:
            input_parts.append(f"\nTURN {self.turn_count + 1} OF 2: Present your opening {self.config.perspective.upper()} argument on the Indian IT/Technology sector:")

        input_message = "\n".join(input_parts)

        try:
            response = self.chain.invoke({
                "history": history_messages,
                "input": input_message
            })

            # Create debate message
            debate_msg = DebateMessage(
                agent_name=self.config.name,
                perspective=self.config.perspective,
                content=response.content,
                turn_number=turn_number
            )

            # Add to conversation history
            self.conversation_history.append(debate_msg)

            logger.info(f"{self.config.name} generated response for turn {turn_number}")
            return debate_msg

        except Exception as e:
            logger.error(f"Error generating response for {self.config.name}: {e}")

            # Fallback response
            fallback_content = f"I apologize, but I encountered an error generating my {self.config.perspective} perspective on the Indian Banking sector. Please check the system configuration."

            return DebateMessage(
                agent_name=self.config.name,
                perspective=self.config.perspective,
                content=fallback_content,
                turn_number=turn_number
            )

class MetaAgent:
    """Enhanced meta agent for stricter analysis and synthesis of multi-agent debates"""
    def __init__(self, model_config, data_loader: FinancialDataLoader):
        self.model_config = model_config
        self.data_loader = data_loader
        self.llm = get_llm_from_config(model_config)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._build_system_prompt()),
            ("human", "{debate_transcript}")
        ])

        self.chain = self.prompt | self.llm

    def _build_system_prompt(self) -> str:
        financial_context = self.data_loader.get_financial_context()

        return f"""You are an ENHANCED META-ANALYST with stricter analytical standards, tasked with synthesizing multi-agent debate perspectives into a rigorous, evidence-based report.

AVAILABLE FINANCIAL DATA:
{financial_context}

Your enhanced mandate is to analyze the complete multi-agent debate transcript on the Indian IT/Technology sector with the following STRICT CRITERIA:

**ANALYTICAL RIGOR REQUIREMENTS:**
1. **TEMPORAL ANALYSIS PRIORITY**: Emphasize the recency and temporal relevance of all data points and arguments
2. **EVIDENCE VALIDATION**: Verify all claims against provided financial data - flag unsupported assertions and note data recency
3. **CHRONOLOGICAL COHERENCE**: Identify internal contradictions within each agent's arguments, especially temporal inconsistencies
4. **CROSS-PERSPECTIVE SYNTHESIS**: Extract genuine insights that emerge from agent interactions, with focus on recent trends
5. **REASONING QUALITY ASSESSMENT**: Evaluate the depth and quality of reasoning chains, prioritizing recent data usage
6. **ACTIONABLE INTELLIGENCE**: Provide decision-ready insights with confidence intervals based on data recency

**ENHANCED REPORT STRUCTURE:**
# Multi-Agent Dialectical Analysis: Indian IT/Technology Sector - September 2025

## Executive Summary
[Concise overview with key findings, confidence levels, and temporal context]

## Temporal Data Analysis
[Assessment of data recency, time periods covered, and chronological relevance of arguments]

## Agent Perspective Analysis
[Detailed analysis of each agent's core arguments, evidence quality, reasoning depth, and temporal focus]

## Evidence Verification Matrix
[Fact-checking of key claims against available financial data with emphasis on data recency and temporal validity]

## Chronological Coherence Assessment
[Evaluation of temporal consistency and time-based reasoning across all agents]

## Recent Trends Synthesis
[Cross-perspective insights focused on latest developments and recent market dynamics]

## Areas of Convergence vs. Genuine Disagreement
[Distinguish between surface-level differences and fundamental disputes, with temporal context]

## Meta-Analysis: What the Recent Data Reveals
[Higher-order insights about current market dynamics and recent sector developments]

## Decision Framework
[Actionable recommendations with probability weightings, risk assessments, and temporal validity]

## Confidence Assessment
[Explicit confidence intervals for key conclusions with data recency confidence ratings]

MAINTAIN ENHANCED OBJECTIVITY: Apply rigorous fact-checking, demand evidence for all claims, and provide probabilistic rather than deterministic conclusions."""

    def synthesize(self, debate_messages: List[DebateMessage]) -> str:
        # Build enhanced debate transcript with meta-analysis context
        transcript_parts = [
            "MULTI-AGENT DEBATE TRANSCRIPT - Indian IT/Technology Sector Analysis",
            "=" * 80,
            f"Total Participants: {len(set(msg.agent_name for msg in debate_messages))}",
            f"Total Exchanges: {len(debate_messages)}",
            f"Agent Turn Distribution: {self._analyze_turn_distribution(debate_messages)}",
            ""
        ]

        # Group messages by agent for better analysis
        agents_summary = {}
        for msg in debate_messages:
            if msg.agent_name not in agents_summary:
                agents_summary[msg.agent_name] = []
            agents_summary[msg.agent_name].append(msg)

        transcript_parts.append("AGENT PARTICIPATION SUMMARY:")
        for agent_name, messages in agents_summary.items():
            transcript_parts.append(f"- {agent_name}: {len(messages)} turns")
        transcript_parts.append("")
        transcript_parts.append("FULL TRANSCRIPT:")
        transcript_parts.append("=" * 80)
        transcript_parts.append("")

        for msg in debate_messages:
            transcript_parts.extend([
                f"Turn {msg.turn_number} - {msg.agent_name} ({msg.perspective.upper()}):",
                "-" * 50,
                msg.content,
                "",
                "=" * 80,
                ""
            ])

        debate_transcript = "\n".join(transcript_parts)

        try:
            response = self.chain.invoke({
                "debate_transcript": debate_transcript
            })

            logger.info("Enhanced meta-analysis report generated successfully")
            return response.content

        except Exception as e:
            logger.error(f"Error generating meta-analysis report: {e}")
            return f"Error generating meta-analysis report: {str(e)}"

    def _analyze_turn_distribution(self, debate_messages: List[DebateMessage]) -> str:
        """Analyze how turns were distributed among agents"""
        agent_turns = {}
        for msg in debate_messages:
            agent_turns[msg.agent_name] = agent_turns.get(msg.agent_name, 0) + 1

        distribution = ", ".join([f"{name}: {count}" for name, count in agent_turns.items()])
        return distribution

# Legacy alias for backwards compatibility
SynthesisAgent = MetaAgent


def load_optimized_persona(persona_type: Literal["calculative", "conservative", "disciplined",
                                                "hybrid", "optimist", "pessimist",
                                                "radical", "speculative"]) -> str:
    """Load optimized persona prompt from markdown files"""
    try:
        file_path = Path(f"optimized_{persona_type}_prompt.md")
        if not file_path.exists():
            logger.warning(f"Optimized prompt file not found: {file_path}")
            return f"You are a {persona_type} financial analyst focused on the Indian Banking sector."

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the actual prompt content (skip metadata)
        lines = content.split('\n')
        prompt_started = False
        prompt_lines = []

        for line in lines:
            if ("## Optimized Prompt" in line or
                "## New Instructions for the Assistant" in line or
                "### New instruction for the assistant" in line or
                "### New Task Instruction for the Assistant" in line or
                "### New task instruction for the assistant" in line or
                "### Objective" in line):
                prompt_started = True
                continue
            elif prompt_started and line.startswith("## Key Improvements"):
                break
            elif prompt_started:
                prompt_lines.append(line)

        if prompt_lines:
            return '\n'.join(prompt_lines).strip()
        else:
            logger.warning(f"Could not extract prompt from {file_path}")
            return f"You are a {persona_type} financial analyst focused on the Indian Banking sector."

    except Exception as e:
        logger.error(f"Error loading optimized persona {persona_type}: {e}")
        return f"You are a {persona_type} financial analyst focused on the Indian Banking sector."


class MultiAgentDebateSystem:
    """Enhanced multi-agent debate system with 8 optimized personas"""

    def __init__(self, data_loader: FinancialDataLoader, model_config):
        self.data_loader = data_loader
        self.model_config = model_config
        self.agents: Dict[str, DebateAgent] = {}
        self.meta_agent = MetaAgent(model_config, data_loader)

        # Initialize all 8 agents with optimized personas
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all 8 optimized persona agents"""
        persona_configs = [
            ("Calculative Analyst", "calculative", "analytical"),
            ("Conservative Investor", "conservative", "defensive"),
            ("Disciplined Strategist", "disciplined", "systematic"),
            ("Hybrid Tactician", "hybrid", "balanced"),
            ("Growth Optimist", "optimist", "bullish"),
            ("Risk Pessimist", "pessimist", "bearish"),
            ("Radical Disruptor", "radical", "contrarian"),
            ("Speculative Trader", "speculative", "opportunistic")
        ]

        for name, persona_type, perspective in persona_configs:
            try:
                system_prompt = load_optimized_persona(persona_type)

                agent_config = AgentConfig(
                    name=name,
                    role=f"{persona_type.title()} Financial Analyst",
                    perspective=perspective,
                    model=self.model_config,
                    system_prompt=system_prompt,
                    max_turns=2  # Constraint: only 2 turns per agent
                )

                self.agents[name] = DebateAgent(agent_config, self.data_loader)
                logger.info(f"Initialized agent: {name}")

            except Exception as e:
                logger.error(f"Failed to initialize agent {name}: {e}")

    def run_debate_round(self, topic: str, max_rounds: int = 2) -> List[DebateMessage]:
        """Run a structured debate with all agents"""
        debate_messages = []
        all_agent_names = list(self.agents.keys())

        logger.info(f"Starting multi-agent debate with {len(all_agent_names)} agents")

        for round_num in range(1, max_rounds + 1):
            logger.info(f"Starting round {round_num}")

            # Shuffle agent order for each round to ensure fairness
            import random
            round_agents = all_agent_names.copy()
            random.shuffle(round_agents)

            for agent_name in round_agents:
                agent = self.agents[agent_name]

                # Check if agent has exceeded turn limit
                if agent.turn_count >= agent.max_turns_per_agent:
                    logger.info(f"Agent {agent_name} has reached maximum turns, skipping")
                    continue

                try:
                    # Get recent messages from other agents for context
                    other_messages = [
                        msg.content for msg in debate_messages[-6:]  # Last 6 messages for context
                        if msg.agent_name != agent_name
                    ]

                    # Generate response
                    response = agent.respond(
                        debate_context=topic,
                        opponent_messages=other_messages if other_messages else None,
                        turn_number=len(debate_messages) + 1
                    )

                    debate_messages.append(response)
                    logger.info(f"Agent {agent_name} contributed turn {response.turn_number}")

                except Exception as e:
                    logger.error(f"Error getting response from {agent_name}: {e}")
                    continue

        logger.info(f"Debate completed with {len(debate_messages)} total messages")
        return debate_messages

    def generate_meta_analysis(self, debate_messages: List[DebateMessage]) -> str:
        """Generate enhanced meta-analysis of the debate"""
        return self.meta_agent.synthesize(debate_messages)

    def get_agent_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about agent participation"""
        stats = {}
        for name, agent in self.agents.items():
            stats[name] = {
                "turns_taken": agent.turn_count,
                "max_turns": agent.max_turns_per_agent,
                "messages_count": len(agent.conversation_history),
                "perspective": agent.config.perspective
            }
        return stats