"""
Workflow graph for the code analysis agent system.

This module creates the LangGraph StateGraph that orchestrates the multi-agent
code analysis workflow with proper node connections and routing.
"""

from typing import Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import WorkflowState
from .nodes import (
    parse_pr_data,
    pr_analysis_agent
)


def create_analysis_workflow() -> StateGraph:
    """
    Create the main PR analysis workflow graph using a single comprehensive agent.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("parse_pr_data", parse_pr_data)
    workflow.add_node("pr_analysis_agent", pr_analysis_agent)
    
    # Set entry point
    workflow.set_entry_point("parse_pr_data")
    
    # Edges
    workflow.add_edge("parse_pr_data", "pr_analysis_agent")
    workflow.add_edge("pr_analysis_agent", END)
    
    return workflow


def compile_workflow(workflow: StateGraph, use_memory: bool = True) -> Any:
    """
    Compile the workflow graph with optional memory persistence.
    
    Args:
        workflow: The StateGraph to compile
        use_memory: Whether to use memory saver for persistence
        
    Returns:
        Compiled workflow graph
    """
    if use_memory:
        # Set up memory saver for workflow state persistence
        memory = MemorySaver()
        compiled_workflow = workflow.compile(checkpointer=memory)
    else:
        compiled_workflow = workflow.compile()
    
    return compiled_workflow


def create_default_workflow() -> Any:
    """
    Create and compile the default analysis workflow.
    
    Returns:
        Compiled workflow ready for execution
    """
    workflow = create_analysis_workflow()
    return compile_workflow(workflow)