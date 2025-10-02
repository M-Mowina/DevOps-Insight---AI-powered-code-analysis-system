"""
Workflow nodes for the PR analysis agent system.

This module contains the PR analysis agent node.
"""

from typing import Dict, Any
import json
from langgraph.prebuilt import create_react_agent
from .state import WorkflowState
from .tools import create_tool_registry


def parse_pr_data(state: WorkflowState) -> WorkflowState:
    """
    Parse the PR JSON stored in state.pr_data and extract `collection_name`.

    Heuristics:
    - Use explicit `collection_name` if present
    - Fallback to common fields like `repository`, `repo`, nested GitHub/Azure styles
    """
    print("🧩 [Parse PR Data] Extracting collection_name from pr_data...")

    try:
        raw = getattr(state, 'pr_data', '')

        # Normalize into a dict
        pr_obj: Dict[str, Any]
        if isinstance(raw, dict):
            pr_obj = raw
        else:
            pr_obj = json.loads(raw or '{}')

        # Candidate extraction functions
        def get_nested(obj: Dict[str, Any], *keys: str) -> Any:
            current: Any = obj
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return None
                current = current[key]
            return current

        # Prefer top-level `repository` explicitly, then common fallbacks.
        candidates = [
            pr_obj.get('repository'),
            get_nested(pr_obj, 'pullRequest', 'repository'),
            get_nested(pr_obj, 'repository', 'name'),
            pr_obj.get('repo'),
            get_nested(pr_obj, 'pull_request', 'base', 'repo', 'name'),
            get_nested(pr_obj, 'pull_request', 'head', 'repo', 'name'),
            # Lowest priority: explicit collection_name override if provided elsewhere
            pr_obj.get('collection_name'),
        ]

        # First non-empty string candidate wins
        collection_name = next((c for c in candidates if isinstance(c, str) and c.strip()), None)

        if collection_name:
            state.collection_name = collection_name.strip()
            print(f"✅ [Parse PR Data] collection_name set to: {state.collection_name}")
        else:
            print("ℹ️ [Parse PR Data] No collection_name found in pr_data")

        state.mark_node_complete("parse_pr_data")
        state.current_step = "parsed_pr_data"

    except Exception as e:
        print(f"❌ [Parse PR Data] Error: {e}")
        import traceback
        traceback.print_exc()
        state.analysis_error = str(e)

    return state


def pr_analysis_agent(state: WorkflowState) -> WorkflowState:
    """
    AI agent node for Pull Request analysis.
    Uses create_react_agent with analysis tools specifically designed for PR review.
    """
    print("🔍 [PR Analysis Agent] Starting PR analysis...")
    
    try:
        # Get available tools
        tools = list(create_tool_registry().values())
        
        # Initialize LLM
        from langchain_openai import ChatOpenAI

        qwen_model = ChatOpenAI(
            model="Areeb-Coder-FP8",
            """🤖 Your LLM of choice for code analysis and review.""" # type: ignore
        )
        # Create the PR analysis agent
        agent = create_react_agent(
            model=qwen_model,
            tools=tools,
            prompt="""You are a Pull Request Analysis Agent.  
Your job is to review code changes in a pull request (PR) for correctness, style, maintainability, and security risks.  
Focus your analysis on the files and diffs provided in the PR, but use the available tools to explore the repository if you need more context.

### Tools available:
- `list_directories`: list all file paths in the repository.  
- `get_metadata_by_id`: inspect metadata for a file without reading its full content.  
- `get_content_by_id`: fetch the actual code of a file for deeper analysis.  
- `search_vector_database`: search semantically for related files or concepts in the repo.  

### How you should work:
1. Start with the PR's title, description, and the diff of changed files.  
2. For each file:
- Check whether the change introduces bugs, vulnerabilities, or regressions.  
- Evaluate code quality (readability, maintainability, adherence to best practices).  
- Verify that tests are updated or added if functionality changes.  
3. If needed, use the tools to get additional context (e.g., fetch the full file or search related files).  
4. Provide your analysis in a structured format.

### Output format:
- **Summary:** High-level impression of the PR (e.g., "Good improvement, but missing test coverage").  
- **Detailed Findings:** For each file/diff:
- File path
- Observed issues (bugs, vulnerabilities, style issues, missing docs/tests)
- Suggested fixes or improvements
- **Security Concerns:** Highlight any vulnerabilities (SQLi, XSS, insecure crypto, etc.).  
- **Recommendation:** Final verdict (approve, approve with changes, request major changes).  

You must base your analysis on actual PR content. If more context is needed, fetch it with the tools before making conclusions. Do not invent issues that are not supported by the code."""
        )
        
        # Get PR data from state
        pr_data = getattr(state, 'pr_data', '{}')
        
        # Run PR analysis with the full PR information
        response = agent.invoke({
            "messages": [
                {"role": "user", "content": f"Analyze this PR:\n{pr_data}"}
            ]
        },
        {"recursion_limit": 50}
        )
        
        # Print the response directly to the terminal
        print("\n" + "=" * 60)
        print("PR ANALYSIS RESULTS")
        print("=" * 60)
        
        # Extract and print the agent's response
        agent_response_content = ""
        if response and 'messages' in response and response['messages']:
            # Get the last message's content
            last_message = response['messages'][-1]
            if hasattr(last_message, 'content') and last_message.content:
                agent_response_content = last_message.content
                print(last_message.content)
            elif isinstance(last_message, dict) and 'content' in last_message:
                agent_response_content = last_message['content']
                print(last_message['content'])
                        
        # Store the agent's response in the state
        state.analysis_response = agent_response_content
        
        print("=" * 60)
        
        # Process response and update state
        state.mark_node_complete("pr_analysis_agent")
        state.current_step = "pr_analysis_complete"
        
        print("✅ [PR Analysis Agent] Analysis complete")
        
    except Exception as e:
        print(f"❌ [PR Analysis Agent] Error: {e}")
        import traceback
        traceback.print_exc()
        state.analysis_error = str(e)
    
    return state