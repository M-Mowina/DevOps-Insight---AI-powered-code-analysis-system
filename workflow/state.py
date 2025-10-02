"""
Workflow state management for the PR analysis agent system.

This module defines the WorkflowState dataclass that maintains the state
throughout the PR analysis workflow.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class WorkflowState:
    """
    Central state object for the PR analysis workflow.
    
    This state is passed to the PR analysis agent and maintains all 
    analysis results and metadata throughout the execution.
    """
    # Input parameters
    collection_name: Optional[str] = None
    
    # PR data for PR analysis workflow
    pr_data: str = ""
    
    # Workflow control
    current_step: str = "start"
    completed_nodes: List[str] = field(default_factory=list)
    
    # Analysis results
    analysis_response: Optional[str] = None
    analysis_error: Optional[str] = None
    
    # Analysis metadata
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize start time when state is created"""
        if self.start_time is None:
            self.start_time = datetime.now()
    
    def mark_node_complete(self, node_name: str) -> None:
        """Mark a workflow node as completed"""
        if node_name not in self.completed_nodes:
            self.completed_nodes.append(node_name)
    
    def is_node_complete(self, node_name: str) -> bool:
        """Check if a workflow node has been completed"""
        return node_name in self.completed_nodes
    
    def finalize_analysis(self) -> None:
        """Mark the analysis as complete and set end time"""
        self.end_time = datetime.now()
        self.current_step = "complete"
    
    @property
    def execution_time(self) -> Optional[float]:
        """Get the total execution time in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_complete(self) -> bool:
        """Check if the workflow is complete"""
        return self.current_step == "complete"