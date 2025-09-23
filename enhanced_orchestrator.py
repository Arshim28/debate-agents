from typing import Dict, Any, List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import logging

from agents import DebateAgent, MetaAgent, DebateMessage, MultiAgentDebateSystem
from config import SystemConfig, ModelConfig
from data_loader import FinancialDataLoader

logger = logging.getLogger(__name__)

class EnhancedDebateState(TypedDict):
    debate_messages: List[DebateMessage]
    current_round: int
    max_rounds: int
    topic: str
    is_complete: bool
    meta_analysis: Optional[str]
    active_agents: List[str]
    agent_stats: Dict[str, Dict[str, Any]]
    reasoning_depth: int

class EnhancedDebateOrchestrator:
    """Enhanced orchestrator for multi-agent debates with reasoning models"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.data_loader = FinancialDataLoader(config.debate.data_directory)

        # Create agent-specific model config (Grok with very high reasoning)
        agent_model_config = ModelConfig(
            model_name="x-ai/grok-4-fast:free",
            temperature=0.3,
            max_tokens=1000,  # 1k tokens for detailed analysis
            api_key_env="OPENROUTER_API_KEY",
            reasoning_effort="high",
            max_reasoning_tokens=15000
        )

        # Initialize enhanced multi-agent system with agent-specific config
        self.debate_system = MultiAgentDebateSystem(
            self.data_loader,
            agent_model_config
        )

        self.meta_agent = MetaAgent(config.synthesis_agent, self.data_loader)

        # Create the enhanced debate graph
        self.checkpointer = MemorySaver()
        self.graph = self._build_enhanced_graph()

        logger.info("Dialectical Agent System initialized with 2 ethos personas")

    def _build_enhanced_graph(self) -> StateGraph:
        graph = StateGraph(EnhancedDebateState)

        # Add nodes for enhanced multi-agent flow
        graph.add_node("initialize_debate", self._initialize_debate_node)
        graph.add_node("conduct_round", self._conduct_round_node)
        graph.add_node("evaluate_progress", self._evaluate_progress_node)
        graph.add_node("meta_analyze", self._meta_analyze_node)

        # Add edges
        graph.add_edge(START, "initialize_debate")
        graph.add_edge("initialize_debate", "conduct_round")

        # Conditional edge for continuing or finishing
        graph.add_conditional_edges(
            "conduct_round",
            self._should_continue_enhanced_debate,
            {
                "continue": "evaluate_progress",
                "complete": "meta_analyze"
            }
        )

        graph.add_edge("evaluate_progress", "conduct_round")
        graph.add_edge("meta_analyze", END)

        return graph.compile(checkpointer=self.checkpointer)

    def _initialize_debate_node(self, state: EnhancedDebateState) -> EnhancedDebateState:
        logger.info("Initializing enhanced multi-agent debate")

        return {
            **state,
            "current_round": 1,
            "max_rounds": 2,  # Only 2 rounds total
            "topic": self.config.debate.topic,
            "is_complete": False,
            "active_agents": list(self.debate_system.agents.keys()),
            "debate_messages": [],
            "meta_analysis": None,
            "agent_stats": {},
            "reasoning_depth": 3  # Enhanced reasoning for reasoning models
        }

    def _conduct_round_node(self, state: EnhancedDebateState) -> EnhancedDebateState:
        logger.info(f"Conducting debate round {state['current_round']}")

        # Enhanced topic with explicit IT/Tech sector guidance and recency emphasis
        enhanced_topic = f"""{state['topic']} - Focus strictly on Indian IT/Technology sector companies, market dynamics, and financial performance.

        CRITICAL TEMPORAL FOCUS:
        - PRIORITIZE RECENT DATA: Emphasize the most recent financial results, quarterly reports, and market developments
        - DATE AWARENESS: Always reference specific time periods, quarters (Q1/Q2/Q3/Q4 FY25), and recent months
        - TEMPORAL TRENDS: Analyze quarter-over-quarter (QoQ) and year-over-year (YoY) changes and trajectories
        - RECENCY RANKING: Give higher weight to data from the latest available periods vs. older historical data
        - CURRENT CONTEXT: Frame analysis within the current market environment and recent industry shifts

        Discuss themes like: digital transformation, AI/ML adoption, cloud migration, talent acquisition costs, client spending patterns, regulatory impacts on tech companies, and competitive positioning - but always with emphasis on RECENT developments and LATEST available data."""

        # Run a complete round with all agents
        round_messages = self.debate_system.run_debate_round(
            topic=enhanced_topic,
            max_rounds=1  # One round at a time
        )

        # Update state with new messages
        updated_messages = state["debate_messages"] + round_messages
        updated_stats = self.debate_system.get_agent_stats()

        return {
            **state,
            "debate_messages": updated_messages,
            "current_round": state["current_round"] + 1,
            "agent_stats": updated_stats
        }

    def _evaluate_progress_node(self, state: EnhancedDebateState) -> EnhancedDebateState:
        logger.info(f"Evaluating debate progress after round {state['current_round'] - 1}")

        # Log current statistics
        for agent_name, stats in state["agent_stats"].items():
            logger.info(f"{agent_name}: {stats['turns_taken']}/{stats['max_turns']} turns")

        # Check if we need to continue
        total_messages = len(state["debate_messages"])
        logger.info(f"Total messages so far: {total_messages}")

        return state

    def _should_continue_enhanced_debate(self, state: EnhancedDebateState) -> str:
        # Check if we've completed the maximum rounds
        if state["current_round"] > state["max_rounds"]:
            logger.info(f"Debate complete after {state['current_round'] - 1} rounds")
            return "complete"

        # Check if all agents have reached their turn limits
        agents_exhausted = all(
            stats['turns_taken'] >= stats['max_turns']
            for stats in state["agent_stats"].values()
        )

        if agents_exhausted:
            logger.info("All agents have reached maximum turns")
            return "complete"

        logger.info(f"Continuing debate - round {state['current_round']} of {state['max_rounds']}")
        return "continue"

    def _meta_analyze_node(self, state: EnhancedDebateState) -> EnhancedDebateState:
        logger.info("Generating enhanced meta-analysis")

        meta_analysis = self.meta_agent.synthesize(state["debate_messages"])

        return {
            **state,
            "meta_analysis": meta_analysis,
            "is_complete": True
        }

    def run_enhanced_debate(self, thread_id: str = "enhanced_debate_thread") -> Dict[str, Any]:
        try:
            # Initial state
            initial_state: EnhancedDebateState = {
                "debate_messages": [],
                "current_round": 0,
                "max_rounds": 2,
                "topic": self.config.debate.topic,
                "is_complete": False,
                "meta_analysis": None,
                "active_agents": [],
                "agent_stats": {},
                "reasoning_depth": 3
            }

            # Run the enhanced debate
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.graph.invoke(initial_state, config)

            logger.info("Enhanced multi-agent debate completed successfully")

            return {
                "status": "completed",
                "debate_messages": final_state["debate_messages"],
                "meta_analysis": final_state["meta_analysis"],
                "total_messages": len(final_state["debate_messages"]),
                "total_rounds": final_state["current_round"] - 1,
                "agent_stats": final_state["agent_stats"],
                "topic": final_state["topic"]
            }

        except Exception as e:
            logger.error(f"Error running enhanced debate: {e}")
            return {
                "status": "error",
                "error": str(e),
                "debate_messages": [],
                "meta_analysis": None
            }

    # Legacy method for backwards compatibility
    def run_debate(self, thread_id: str = "debate_thread") -> Dict[str, Any]:
        return self.run_enhanced_debate(thread_id)

    def get_debate_summary(self, result: Dict[str, Any]) -> str:
        if result["status"] == "error":
            return f"Enhanced debate failed with error: {result['error']}"

        summary_parts = [
            f"ENHANCED MULTI-AGENT DEBATE SUMMARY",
            "=" * 80,
            f"Topic: {result.get('topic', 'Unknown')}",
            f"Total Messages: {result.get('total_messages', 0)}",
            f"Total Rounds: {result.get('total_rounds', 0)}",
            f"Status: {result['status'].upper()}",
            "",
            "AGENT PARTICIPATION:",
            "-" * 40
        ]

        # Add agent statistics
        agent_stats = result.get("agent_stats", {})
        for agent_name, stats in agent_stats.items():
            summary_parts.append(
                f"{agent_name}: {stats['turns_taken']}/{stats['max_turns']} turns ({stats['perspective']})"
            )

        summary_parts.extend([
            "",
            "DEBATE FLOW:",
            "-" * 40
        ])

        for msg in result.get("debate_messages", []):
            perspective_marker = f"[{msg.perspective.upper()}]"
            summary_parts.append(f"Turn {msg.turn_number}: {msg.agent_name} {perspective_marker}")
            preview = msg.content[:120].replace('\n', ' ').strip() + "..."
            summary_parts.append(f"   {preview}")
            summary_parts.append("")

        summary_parts.extend([
            "META-ANALYSIS GENERATED: " + ("Yes" if result.get("meta_analysis") else "No"),
            ""
        ])

        return "\n".join(summary_parts)

# Alias for backwards compatibility
DialecticalDebateOrchestrator = EnhancedDebateOrchestrator