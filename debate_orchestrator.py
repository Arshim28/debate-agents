from typing import Dict, Any, List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import logging

from agents import DebateAgent, SynthesisAgent, DebateMessage
from config import SystemConfig
from data_loader import FinancialDataLoader

logger = logging.getLogger(__name__)

class DebateState(TypedDict):
    debate_messages: List[DebateMessage]
    current_turn: int
    max_turns: int
    topic: str
    is_complete: bool
    synthesis_report: Optional[str]
    active_agent: str

class DialecticalDebateOrchestrator:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.data_loader = FinancialDataLoader(config.debate.data_directory)

        # Initialize agents
        self.bull_agent = DebateAgent(config.bull_agent, self.data_loader)
        self.bear_agent = DebateAgent(config.bear_agent, self.data_loader)
        self.synthesis_agent = SynthesisAgent(config.synthesis_agent, self.data_loader)

        # Create the debate graph
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

        logger.info("Dialectical Debate Orchestrator initialized")

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(DebateState)

        # Add nodes
        graph.add_node("start_debate", self._start_debate_node)
        graph.add_node("bull_turn", self._bull_agent_node)
        graph.add_node("bear_turn", self._bear_agent_node)
        graph.add_node("check_completion", self._check_completion_node)
        graph.add_node("synthesize", self._synthesize_node)

        # Add edges
        graph.add_edge(START, "start_debate")
        graph.add_edge("start_debate", "bull_turn")

        # Conditional edges for alternating turns
        graph.add_conditional_edges(
            "bull_turn",
            self._should_continue_debate,
            {
                "continue": "bear_turn",
                "complete": "synthesize"
            }
        )

        graph.add_conditional_edges(
            "bear_turn",
            self._should_continue_debate,
            {
                "continue": "bull_turn",
                "complete": "synthesize"
            }
        )

        graph.add_edge("synthesize", END)

        return graph.compile(checkpointer=self.checkpointer)

    def _start_debate_node(self, state: DebateState) -> DebateState:
        logger.info("Starting dialectical debate")

        return {
            **state,
            "current_turn": 1,
            "max_turns": self.config.debate.max_debate_turns,
            "topic": self.config.debate.topic,
            "is_complete": False,
            "active_agent": "bull",
            "debate_messages": [],
            "synthesis_report": None
        }

    def _bull_agent_node(self, state: DebateState) -> DebateState:
        logger.info(f"Bull agent turn {state['current_turn']}")

        # Get opponent's last message if available
        opponent_message = None
        if state["debate_messages"]:
            last_bear_messages = [msg for msg in state["debate_messages"] if msg.perspective == "bear"]
            if last_bear_messages:
                opponent_message = last_bear_messages[-1].content

        # Generate bull response
        debate_msg = self.bull_agent.respond(
            debate_context=state["topic"],
            opponent_message=opponent_message,
            turn_number=state["current_turn"]
        )

        # Update state
        updated_messages = state["debate_messages"] + [debate_msg]

        return {
            **state,
            "debate_messages": updated_messages,
            "active_agent": "bear"
        }

    def _bear_agent_node(self, state: DebateState) -> DebateState:
        logger.info(f"Bear agent turn {state['current_turn']}")

        # Get opponent's last message
        opponent_message = None
        if state["debate_messages"]:
            last_bull_messages = [msg for msg in state["debate_messages"] if msg.perspective == "bull"]
            if last_bull_messages:
                opponent_message = last_bull_messages[-1].content

        # Generate bear response
        debate_msg = self.bear_agent.respond(
            debate_context=state["topic"],
            opponent_message=opponent_message,
            turn_number=state["current_turn"]
        )

        # Update state
        updated_messages = state["debate_messages"] + [debate_msg]

        return {
            **state,
            "debate_messages": updated_messages,
            "current_turn": state["current_turn"] + 1,
            "active_agent": "bull"
        }

    def _should_continue_debate(self, state: DebateState) -> str:
        if state["current_turn"] > state["max_turns"]:
            logger.info(f"Debate complete after {state['current_turn'] - 1} turns")
            return "complete"

        logger.info(f"Continuing debate - turn {state['current_turn']} of {state['max_turns']}")
        return "continue"

    def _check_completion_node(self, state: DebateState) -> DebateState:
        is_complete = state["current_turn"] > state["max_turns"]
        return {
            **state,
            "is_complete": is_complete
        }

    def _synthesize_node(self, state: DebateState) -> DebateState:
        logger.info("Generating synthesis report")

        synthesis_report = self.synthesis_agent.synthesize(state["debate_messages"])

        return {
            **state,
            "synthesis_report": synthesis_report,
            "is_complete": True
        }

    def run_debate(self, thread_id: str = "debate_thread") -> Dict[str, Any]:
        try:
            # Initial state
            initial_state: DebateState = {
                "debate_messages": [],
                "current_turn": 0,
                "max_turns": self.config.debate.max_debate_turns,
                "topic": self.config.debate.topic,
                "is_complete": False,
                "synthesis_report": None,
                "active_agent": "bull"
            }

            # Run the debate
            config = {"configurable": {"thread_id": thread_id}}
            final_state = self.graph.invoke(initial_state, config)

            logger.info("Debate completed successfully")

            return {
                "status": "completed",
                "debate_messages": final_state["debate_messages"],
                "synthesis_report": final_state["synthesis_report"],
                "total_turns": len(final_state["debate_messages"]),
                "topic": final_state["topic"]
            }

        except Exception as e:
            logger.error(f"Error running debate: {e}")
            return {
                "status": "error",
                "error": str(e),
                "debate_messages": [],
                "synthesis_report": None
            }

    def get_debate_summary(self, result: Dict[str, Any]) -> str:
        if result["status"] == "error":
            return f"Debate failed with error: {result['error']}"

        summary_parts = [
            f"DIALECTICAL DEBATE SUMMARY",
            "=" * 60,
            f"Topic: {result.get('topic', 'Unknown')}",
            f"Total Exchanges: {result.get('total_turns', 0)}",
            f"Status: {result['status'].upper()}",
            "",
            "DEBATE FLOW:",
            "-" * 30
        ]

        for i, msg in enumerate(result.get("debate_messages", []), 1):
            perspective_marker = "[BULL]" if msg.perspective == "bull" else "[BEAR]"
            summary_parts.append(f"Turn {msg.turn_number}: {msg.agent_name} {perspective_marker}")
            preview = msg.content[:100].replace('\n', ' ').strip() + "..."
            summary_parts.append(f"   {preview}")
            summary_parts.append("")

        summary_parts.extend([
            "SYNTHESIS REPORT GENERATED: " + ("Yes" if result.get("synthesis_report") else "No"),
            ""
        ])

        return "\n".join(summary_parts)