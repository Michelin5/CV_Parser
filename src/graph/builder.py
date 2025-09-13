from langgraph.graph import StateGraph, END
from agents import agent0_validator, agent1_extractor
from src.graph.state import AgentState


def should_continue(state):
    """
    Determines whether to continue to the extractor node or end the workflow.
    Args:
        state: The current state of the graph
    Returns:
        The next node to execute
    """
    validation_result = state.get("validation_result")

    if validation_result and validation_result.get("is_resume", False):
        return "extractor"

    return END


def create_workflow():
    """
    Creates and compiles the LangGraph workflow for resume processing.
    Returns:
        Compiled workflow
    """
    # Initialize graph with state
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("validator", lambda state: {"validation_result": agent0_validator(state["file_content"])})
    workflow.add_node("extractor", lambda state: {"extraction_result": agent1_extractor(state["file_content"])})

    # Set entry point
    workflow.set_entry_point("validator")

    # Add conditional edges
    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "extractor": "extractor",
            END: END
        }
    )

    # Add edge from extractor to end
    workflow.add_edge("extractor", END)

    # Compile the graph
    return workflow.compile()
