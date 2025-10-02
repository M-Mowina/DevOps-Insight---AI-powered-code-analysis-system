#!/usr/bin/env python3
"""
Main entry point for the DevOps Insight PR analysis workflow.
"""

import sys
import os
import json

# Add project root to path for imports
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'workflow'))

from workflow.graph import create_default_workflow
from workflow.state import WorkflowState


def main():
    """Run the PR analysis workflow with sample data."""
    print("=" * 60)
    print("DevOps Insight - PR Analysis Workflow")
    print("=" * 60)
    
    # Sample PR data for testing
    json_pr_data = {
        "pullRequest": {
            "id": 7,
            "title": "Merge pull request #7 from feature/json-file-output into master",
            "description": "PR submitted from Azure DevOps pipeline",
            "status": "active",
            "author": "Sherif Asker",
            "sourceBranch": "refs/heads/feature/json-file-output",
            "targetBranch": "refs/heads/master",
            "repository": "pr-api"
        },
        "commits": [
            {
                "id": "f9f6b6bac89e7e3def9de1dd3a4f9e8894fe4f9c",
                "message": "Update API endpoint port in azure-pipelines.yml from 3333 to 8050",
                "author": "Sherif Asker"
            },
            {
                "id": "9065d11397027dd42150e522dd1ef4c53ed65974",
                "message": "Update CHANGELOG.md to include a new entry for JSON export feature and additional testing notes.",
                "author": "Sherif Asker"
            }
        ],
        "filesChanged": [
            {
                "filePath": "pr_api.py",
                "changeType": "modified",
                "content": "Added JSON export functionality with aiofiles"
            },
            {
                "filePath": "requirements.txt",
                "changeType": "modified",
                "content": "Added aiofiles dependency"
            }
        ]
    }
    
    try:
        # Create workflow
        print("Initializing PR analysis workflow...")
        app = create_default_workflow()
        print("✅ PR analysis workflow created successfully")
        
        # Create initial state
        collection_name = json_pr_data["pullRequest"]["repository"]
        state = WorkflowState(
            collection_name=collection_name,
            pr_data=json.dumps(json_pr_data, indent=2)
        )
        print(f"✅ Created workflow state for collection: {state.collection_name}")
        
        # Run the workflow
        print("\n🚀 Running PR analysis workflow...")
        final_state = app.invoke(state, {"configurable": {"thread_id": json_pr_data["pullRequest"]["id"]}})
        
        # Display results
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Current step: {app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['current_step']}")
        print(f"Completed nodes: {app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['completed_nodes']}")
        if app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['analysis_response']:
            print(f"Analysis response: {app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['analysis_response'][:500]}...")
        else:
            print("No analysis response generated")
        if app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['analysis_error']:
            print(f"Analysis error: {app.get_state({'configurable': {'thread_id': json_pr_data['pullRequest']['id']}}).values['analysis_error']}")
        
        print("\n✅ Workflow execution completed")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Workflow failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)