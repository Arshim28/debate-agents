from typing import Dict, Any, List, Optional
from typing_extensions import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
import logging
from pathlib import Path

from config import AgentConfig, get_llm_from_config
from intelligent_data_loader import IntelligentFinancialDataLoader
from date_utils import get_current_financial_context, get_previous_quarters

logger = logging.getLogger(__name__)

class DebateMessage(BaseModel):
    agent_name: str
    perspective: str
    content: str
    turn_number: int
    timestamp: str = Field(default_factory=lambda: str(__import__('datetime').datetime.now()))

class DebateAgent:
    def __init__(self, config: AgentConfig, data_loader: IntelligentFinancialDataLoader):
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

    def _formulate_and_execute_queries(self, debate_context: str, opponent_messages: Optional[List[str]] = None, turn_number: int = 1) -> str:
        """
        MISSION CRITICAL: Dynamically query data connectors for current market intelligence.
        NO FALLBACKS - Must succeed with all 3 queries or fail clearly.
        """
        # Get dynamic financial context
        fin_context = get_current_financial_context()

        # Dynamic query formulation - NO FALLBACKS, will raise if fails
        base_queries = self._generate_dynamic_queries(debate_context, opponent_messages, turn_number)

        # Execute queries and gather fresh intelligence
        fresh_intelligence_parts = [
            "FRESH MARKET INTELLIGENCE - DYNAMIC DATA GATHERING:",
            "=" * 70,
            f"Query Execution Time: {fin_context['current_date_str']} {fin_context['current_date'].strftime('%H:%M:%S')}",
            f"Agent Perspective: {self.config.perspective.upper()}",
            f"Financial Context: {fin_context['quarter_period']}",
            f"Turn Number: {turn_number}",
            f"Dynamic Queries: {len(base_queries)}/3",
            "",
            "REAL-TIME DATA SOURCES:",
            "=" * 30
        ]

        successful_queries = 0

        # Execute all 3 dynamic queries with throttling - Continue on errors but track them
        for i, query in enumerate(base_queries, 1):
            logger.info(f"{self.config.name} executing dynamic query {i}/3: {query[:50]}...")

            # Add throttling delay to prevent API overload
            import time
            time.sleep(2)  # 2-second delay to prevent rate limiting

            try:
                # Get multi-source intelligence
                query_result = self.data_loader.get_intelligent_context(query)

                if query_result and len(query_result.strip()) >= 50:
                    fresh_intelligence_parts.extend([
                        f"\n🔍 DYNAMIC QUERY {i}: {query}",
                        "-" * 50,
                        query_result[:1000] + "..." if len(query_result) > 1000 else query_result,
                        "",
                        "=" * 70,
                        ""
                    ])
                    successful_queries += 1
                else:
                    logger.warning(f"Query {i} returned insufficient data: {len(query_result) if query_result else 0} characters")
                    fresh_intelligence_parts.extend([
                        f"\n⚠️ QUERY {i} - INSUFFICIENT DATA: {query}",
                        "-" * 50,
                        "Data source returned insufficient information for this query.",
                        "",
                        "=" * 70,
                        ""
                    ])

            except Exception as e:
                logger.warning(f"Query {i} failed: {e}")
                fresh_intelligence_parts.extend([
                    f"\n❌ QUERY {i} - DATA UNAVAILABLE: {query}",
                    "-" * 50,
                    f"Data source error: {str(e)[:100]}",
                    "",
                    "=" * 70,
                    ""
                ])

        fresh_intelligence = "\n".join(fresh_intelligence_parts)

        # Log success rate but continue regardless
        logger.info(f"{self.config.name} completed {successful_queries}/3 queries successfully")
        return fresh_intelligence


    def _build_system_prompt(self) -> str:
        # Get dynamic financial context
        fin_context = get_current_financial_context()
        prev_quarters = get_previous_quarters(fin_context, 3)

        return f"""{self.config.system_prompt}

🚨 MISSION CRITICAL DATA MANDATE:
You are a {self.config.perspective.upper()} analyst with MANDATORY access to FRESH MARKET INTELLIGENCE.
Before each response, you will receive REAL-TIME data queries executed specifically for this debate turn.

📅 CURRENT FINANCIAL CONTEXT:
• Date: {fin_context['current_date_str']}
• Financial Year: {fin_context['financial_year_full']}
• Current Quarter: {fin_context['quarter_period']}
• Previous Quarters: {', '.join(prev_quarters)}
• Half Year: {fin_context['half_year_full']}

⚠️  ABSOLUTE PROHIBITION: DO NOT use training data, general knowledge, or outdated information.
✅ MANDATORY REQUIREMENT: Use ONLY the fresh market intelligence provided in each prompt.

📊 MULTI-MODAL INTELLIGENCE SOURCES:
• ChromaDB RAG System: Proprietary research documents (HIGHEST PRIORITY)
• Jina Web Search: Real-time market intelligence
• YouTube Connector: Expert interviews and commentary
• Market Indices: Live financial data (when available)

🎯 DEBATE INSTRUCTIONS - FRESH DATA DRIVEN ANALYSIS:
- You are participating in a structured multi-agent debate about the Indian IT/Technology sector
- SECTOR FOCUS: Keep ALL discussions centered on IT/Technology companies, trends, and market dynamics
- ANALYTICAL FOCUS: This is a sectoral assessment, NOT investment advice - focus on business fundamentals

🔥 FRESH DATA ENFORCEMENT (MISSION CRITICAL):
  * ZERO TOLERANCE for training data usage - use ONLY fresh intelligence provided
  * MANDATORY DATE CITATIONS: Every claim must include 'as of [specific date]' from fresh data
  * QUERY-DRIVEN RESPONSES: Base arguments exclusively on the real-time queries executed for you
  * SOURCE VALIDATION: Reference specific data sources (RAG documents, web search, market indices)
  * RECENCY VERIFICATION: Only cite {fin_context['quarter_full']}, {prev_quarters[0]}, {fin_context['half_year_full']} data
  * TEMPORAL PRECISION: Use exact dates, quarters, and timeframes from fresh intelligence

📊 RESPONSE CONSTRUCTION PROTOCOL:
1. Start with fresh data analysis from the provided intelligence
2. Cite specific metrics with exact dates and sources
3. Build arguments using only current market developments
4. Counter opponents with recent data contradictions
5. Maintain your {self.config.perspective.upper()} perspective using fresh evidence

🔒 CRITICAL CONSTRAINTS:
  * MAX 2000 tokens per response - use them strategically
  * EXACTLY 2 turns in this debate
  * Fresh data citations MANDATORY for every factual claim
  * Focus on current {fin_context['financial_year_str']} developments

🎪 SECTOR THEMES (Using Fresh Data Only):
- Indian IT sector performance vs broader market (Nifty IT vs Nifty 50)
- Local industry dynamics: revenue patterns, margin pressures, client concentration
- Sector-specific regulatory changes affecting operations and costs
- Technology disruption within Indian IT services landscape
- Competitive positioning among Indian IT companies
- Skills availability and wage inflation in local talent market
- Government policy impact on domestic IT sector growth
- Quarterly earnings trends and guidance revisions within IT sector

🚫 PROHIBITED CONTENT: Investment advice, portfolio recommendations, buy/sell guidance
✅ REQUIRED FORMAT: Evidence-based arguments with mandatory fresh data citations

Remember: Your credibility depends on using ONLY the fresh market intelligence provided. Training data usage will invalidate your argument."""

    def respond(self, debate_context: str, opponent_messages: Optional[List[str]] = None, turn_number: int = 1) -> DebateMessage:
        logger.info(f"{self.config.name} starting 2-phase response generation...")

        # PHASE 1: MANDATORY DATA GATHERING - Query connectors for fresh intelligence
        logger.info(f"{self.config.name} Phase 1: Executing mandatory data queries...")
        fresh_market_intelligence = self._formulate_and_execute_queries(
            debate_context, opponent_messages, turn_number
        )

        # PHASE 2: INFORMED RESPONSE GENERATION - Use fresh data to formulate arguments
        logger.info(f"{self.config.name} Phase 2: Generating informed response with fresh data...")

        history_messages = []

        # Add conversation history
        for msg in self.conversation_history[-4:]:  # Keep last 4 messages for context
            if msg.agent_name == self.config.name:
                history_messages.append(AIMessage(content=msg.content))
            else:
                history_messages.append(HumanMessage(content=f"[{msg.agent_name}]: {msg.content}"))

        # Get dynamic financial context
        fin_context = get_current_financial_context()
        prev_quarters = get_previous_quarters(fin_context, 3)

        # Build input message with MANDATORY fresh data inclusion
        input_parts = [
            f"DEBATE CONTEXT: {debate_context}",
            "",
            "📅 CURRENT DATE CONTEXT:",
            f"- Today: {fin_context['current_date_str']}",
            f"- Current Financial Year: {fin_context['financial_year_full']}",
            f"- Current Quarter: {fin_context['quarter_period']}",
            f"- Current Half Year: {fin_context['half_year_full']}",
            f"- Previous Quarters: {', '.join(prev_quarters)}",
            f"- Focus on {fin_context['quarter_full']}, {fin_context['half_year_full']} data",
            "",
            "🚨 CRITICAL: You MUST base your response on the FRESH MARKET INTELLIGENCE below.",
            "DO NOT rely on training data. Use ONLY the recent data provided.",
            "",
            fresh_market_intelligence,
            "",
            "📋 MANDATORY REQUIREMENTS:",
            "- Cite specific dates, quarters, and recent developments from the fresh data above",
            "- Reference exact metrics, figures, and trends from current sources",
            "- Include 'as of [specific date]' for all market claims",
            f"- Focus on {fin_context['quarter_full']}, {prev_quarters[0]} data and recent months",
            "- Prioritize proprietary research reports (RAG data) over web sources",
            "- Reject outdated information - use only the fresh intelligence gathered",
            ""
        ]

        if opponent_messages:
            input_parts.extend([
                "OTHER PARTICIPANTS' ARGUMENTS:",
                "=" * 40
            ])
            for i, msg in enumerate(opponent_messages[-3:], 1):  # Only last 3 messages for context
                input_parts.append(f"\n{i}. {msg}")
            input_parts.extend([
                "",
                f"🎯 TURN {self.turn_count + 1} OF 2: Counter the above arguments using the FRESH DATA.",
                f"Maintain your {self.config.perspective.upper()} perspective with current evidence from the intelligence gathered above."
            ])
        else:
            input_parts.extend([
                f"🎯 TURN {self.turn_count + 1} OF 2: Present your opening {self.config.perspective.upper()} argument.",
                "Base ALL claims on the FRESH MARKET INTELLIGENCE provided above with specific dates and sources."
            ])

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

            # Add to conversation history and increment turn count
            self.conversation_history.append(debate_msg)
            self.turn_count += 1

            logger.info(f"{self.config.name} generated data-driven response for turn {turn_number} using fresh market intelligence")
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

    def _generate_dynamic_queries(self, debate_context: str, opponent_messages: Optional[List[str]] = None, turn_number: int = 1) -> List[str]:
        """
        Generate up to 3 dynamic queries based on debate context and opponent arguments.
        Uses LLM to formulate targeted queries with dynamic date awareness.
        NO FALLBACKS - This must succeed or fail clearly.
        """
        # Get dynamic financial context
        fin_context = get_current_financial_context()
        prev_quarters = get_previous_quarters(fin_context, 2)

        # Build context for query generation
        context_parts = [
            f"Agent Perspective: {self.config.perspective}",
            f"Turn Number: {turn_number}",
            f"Debate Context: {debate_context}",
        ]

        if opponent_messages:
            context_parts.extend([
                "Opponent Arguments:",
                "\n".join(opponent_messages[-2:])  # Last 2 opponent messages
            ])

        query_generation_prompt = f"""
You are a {self.config.perspective} financial analyst in a debate about the Indian IT sector.
Generate EXACTLY 3 specific, targeted queries to gather market intelligence that will help you respond effectively.

CRITICAL DATE CONTEXT:
- Current Date: {fin_context['current_date_str']}
- Current Financial Year: {fin_context['financial_year_full']}
- Current Quarter: {fin_context['quarter_period']}
- Previous Quarters: {', '.join(prev_quarters)}
- Half Year: {fin_context['half_year_full']}

Context:
{chr(10).join(context_parts)}

Rules:
1. Generate EXACTLY 3 queries (no more, no less)
2. Focus on SECTOR-LEVEL trends, policies, and macroeconomic factors (NOT individual companies)
3. Target themes: government policies, industry transformation, regulatory changes, global trends
4. Queries should align with your {self.config.perspective} perspective
5. If responding to opponent, focus on finding sector data to counter their arguments
6. PRIORITIZE proprietary research reports and policy analysis
7. Use current financial terminology: {fin_context['quarter_full']}, {fin_context['half_year_full']}

Query Examples:
- "Nifty IT vs Nifty 50 performance comparison {fin_context['quarter_full']} sector relative strength"
- "Indian IT sector quarterly earnings revenue trends {fin_context['quarter_full']} margin analysis"
- "IT sector local market dynamics client concentration risks {fin_context['quarter_full']} competitive positioning"

Return EXACTLY 3 queries, one per line:
"""

        response = self.llm.invoke(query_generation_prompt)

        # Parse queries from response - NO FALLBACKS
        queries = []
        for line in response.content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith(('1.', '2.', '3.', '-', '•')):
                queries.append(line)
            elif line and (line.startswith(('1.', '2.', '3.', '-', '•'))):
                # Remove numbering/bullets
                clean_query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if clean_query:
                    queries.append(clean_query)

        # Limit to exactly 3 queries - NO FALLBACKS, must succeed
        queries = queries[:3]

        if len(queries) < 1:
            raise ValueError(f"Query generation failed: No queries generated from LLM response")

        # Ensure exactly 3 queries - pad with sector-focused queries if needed
        sector_queries_bullish = [
            f"Nifty IT sector outperformance vs Nifty 50 {fin_context['quarter_full']} relative strength analysis",
            f"Indian IT companies revenue growth margin expansion {fin_context['quarter_full']} quarterly results",
            f"IT sector local market leadership technology adoption {fin_context['quarter_full']} competitive advantages"
        ]

        sector_queries_bearish = [
            f"Nifty IT underperformance vs Nifty 50 {fin_context['quarter_full']} sector weakness indicators",
            f"Indian IT sector margin pressure wage inflation {fin_context['quarter_full']} cost challenges",
            f"IT sector client concentration risks demand slowdown {fin_context['quarter_full']} earnings decline"
        ]

        while len(queries) < 3:
            if self.config.perspective == "bullish":
                queries.append(sector_queries_bullish[(len(queries) - 1) % len(sector_queries_bullish)])
            else:
                queries.append(sector_queries_bearish[(len(queries) - 1) % len(sector_queries_bearish)])

        logger.info(f"{self.config.name} generated {len(queries)} dynamic queries")
        return queries

class MetaAgent:
    """Meta agent for stricter analysis and synthesis of multi-agent debates"""
    def __init__(self, model_config, data_loader: IntelligentFinancialDataLoader):
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

MAINTAIN RIGOROUS OBJECTIVITY: Apply rigorous fact-checking, demand evidence for all claims, and provide probabilistic rather than deterministic conclusions."""

    def synthesize(self, debate_messages: List[DebateMessage]) -> str:
        # Build comprehensive debate transcript with meta-analysis context
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

            logger.info("Comprehensive meta-analysis report generated successfully")
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
            # Look for actual sections in the ethos files
            if ("## Agent Ethos" in line or
                "## Core Beliefs" in line or
                "## Methodology" in line or
                line.startswith("**Axiom")):
                prompt_started = True
                if not line.startswith("**Axiom"):
                    continue  # Skip the header line itself
            elif prompt_started and (line.startswith("## ") and "Agent Ethos" not in line):
                break  # Stop at next major section
            elif prompt_started or line.startswith("**Axiom"):
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

    def __init__(self, data_loader: IntelligentFinancialDataLoader, model_config):
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
        """Generate comprehensive meta-analysis of the debate"""
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