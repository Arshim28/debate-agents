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
- ANALYTICAL FOCUS: This is a sectoral assessment, NOT investment advice - focus on business fundamentals, industry trends, and competitive dynamics
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
- AVOID: Portfolio allocation recommendations, investment advice, or specific buy/sell guidance
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

        return f"""You are a META-ANALYST tasked with synthesizing the dialectical debate between Growth Believer and Cynic into a comprehensive, evidence-based report on the Indian IT/Technology sector.

AVAILABLE FINANCIAL DATA:
{financial_context}

**ANALYTICAL REQUIREMENTS:**
1. **Sectoral Analysis**: Provide comprehensive assessment of Indian IT/Technology sector dynamics and outlook
2. **Dialectical Synthesis**: Analyze the interaction between Growth Believer's optimistic case and Cynic's skeptical challenges
3. **Business Fundamentals**: Assess revenue trends, margin dynamics, competitive positioning, and operational metrics
4. **Risk Assessment**: Evaluate key sector risks, regulatory impacts, and structural challenges
5. **Market Outlook**: Synthesize sector trajectory and key themes based on evidence presented

**CRITICAL CONSTRAINTS:**
- This is a SECTORAL ASSESSMENT REPORT, NOT investment advice
- DO NOT include: buy/sell/hold recommendations, portfolio allocation advice, position sizing, or investment decisions
- DO NOT include: decision frameworks, confidence assessments, or action tables
- FOCUS ON: business fundamentals, industry trends, competitive dynamics, and market analysis

**REPORT STRUCTURE AND FORMATTING GUIDELINES:**

# Sectoral Assessment Report: Indian IT/Technology Sector

## Executive Summary
[Clear, decisive overview of the sector's current state and outlook based on the debate]

## Core Thesis Confrontation
### Growth Believer's Optimistic Case
[Key growth arguments, structural drivers, and positive trends]

### Cynic's Risk Assessment
[Key concerns, structural challenges, and negative trends]

### Dialectical Resolution
[How the arguments interact, where they converge/diverge, and the balanced sectoral view]

## Sector Fundamentals Analysis
[Revenue trends, margin dynamics, competitive positioning, and operational metrics]

## Key Risk Factors
[Regulatory impacts, technological disruption, competitive threats, and structural challenges]

## Market Outlook and Trends
[Sector trajectory, emerging themes, and key developments to monitor]

**FORMATTING STANDARDS:**
- Use **bold** only for section headers and key metrics
- Use *italics* sparingly for emphasis on critical insights or contrarian points
- Employ clear paragraph breaks and logical flow
- Include quantitative data and trends where available
- Maintain professional, analytical tone throughout
- End with sector outlook summary, NOT investment recommendations

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


def load_ethos_persona(persona_type: Literal["growth_believer", "cynic"]) -> str:
    """Load ethos persona prompt from markdown files"""
    try:
        file_path = Path(f"ethos_{persona_type}_prompt.md")
        if not file_path.exists():
            logger.warning(f"Ethos prompt file not found: {file_path}")
            return f"You are a {persona_type} financial analyst focused on the Indian IT/Technology sector."

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
            return f"You are a {persona_type} financial analyst focused on the Indian IT/Technology sector."

    except Exception as e:
        logger.error(f"Error loading ethos persona {persona_type}: {e}")
        return f"You are a {persona_type} financial analyst focused on the Indian Banking sector."


class MultiAgentDebateSystem:
    """Dialectical Agent System with 2 Ethos Personas: Growth Believer and Cynic"""

    def __init__(self, data_loader: FinancialDataLoader, model_config):
        self.data_loader = data_loader
        self.model_config = model_config
        self.agents: Dict[str, DebateAgent] = {}
        self.meta_agent = MetaAgent(model_config, data_loader)

        # Initialize 2 ethos-based agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize 2 ethos-based persona agents"""
        persona_configs = [
            ("Growth Believer", "growth_believer", "bullish"),
            ("Cynic", "cynic", "bearish")
        ]

        for name, persona_type, perspective in persona_configs:
            try:
                system_prompt = load_ethos_persona(persona_type)

                agent_config = AgentConfig(
                    name=name,
                    role=f"{name} Analyst",
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
        """Run a structured dialectical debate with direct agent-to-agent exchanges"""
        debate_messages = []

        # Get the two agents
        growth_believer = self.agents.get("Growth Believer")
        cynic = self.agents.get("Cynic")

        if not growth_believer or not cynic:
            logger.error("Both Growth Believer and Cynic agents must be initialized")
            return debate_messages

        logger.info("Starting dialectical debate with direct agent-to-agent exchanges")

        # Round 1: Opening statements
        logger.info("Round 1: Opening statements")

        # Growth Believer opens
        try:
            response = growth_believer.respond(
                debate_context=topic,
                opponent_messages=None,
                turn_number=1
            )
            debate_messages.append(response)
            logger.info(f"Growth Believer presented opening statement")
        except Exception as e:
            logger.error(f"Error getting opening from Growth Believer: {e}")

        # Cynic responds
        try:
            growth_message = [debate_messages[-1].content] if debate_messages else None
            response = cynic.respond(
                debate_context=topic,
                opponent_messages=growth_message,
                turn_number=2
            )
            debate_messages.append(response)
            logger.info(f"Cynic presented opening statement")
        except Exception as e:
            logger.error(f"Error getting opening from Cynic: {e}")

        # Round 2: Targeted rebuttals (only if both agents have remaining turns)
        if (growth_believer.turn_count < growth_believer.max_turns_per_agent and
            cynic.turn_count < cynic.max_turns_per_agent and len(debate_messages) >= 2):

            logger.info("Round 2: Targeted rebuttals")

            # Growth Believer rebuttal
            try:
                cynic_messages = [msg.content for msg in debate_messages if msg.agent_name == "Cynic"]
                response = growth_believer.respond(
                    debate_context=topic,
                    opponent_messages=cynic_messages,
                    turn_number=len(debate_messages) + 1
                )
                debate_messages.append(response)
                logger.info(f"Growth Believer presented rebuttal")
            except Exception as e:
                logger.error(f"Error getting rebuttal from Growth Believer: {e}")

            # Cynic counter-rebuttal
            try:
                growth_messages = [msg.content for msg in debate_messages if msg.agent_name == "Growth Believer"]
                response = cynic.respond(
                    debate_context=topic,
                    opponent_messages=growth_messages,
                    turn_number=len(debate_messages) + 1
                )
                debate_messages.append(response)
                logger.info(f"Cynic presented counter-rebuttal")
            except Exception as e:
                logger.error(f"Error getting counter-rebuttal from Cynic: {e}")

        logger.info(f"Dialectical debate completed with {len(debate_messages)} exchanges")
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