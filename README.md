# AI-Powered Code Analysis System & PR Monitoring

An intelligent code analysis system that combines semantic search with AI agentic workflows for automated Pull Request review and code analysis. Clone GitHub or Azure DevOps repositories, store them in a vector database, and perform intelligent semantic searches across your codebase with AI-powered analysis.

## Features

- **Multi-Platform Support**: Clone from GitHub and Azure DevOps repositories
- **Semantic Search**: Use natural language queries to find relevant code
- **Vector Storage**: Efficient storage and retrieval using Supabase vector database
- **AI-Powered PR Analysis**: Automated Pull Request review using agentic workflows
- **Smart File Filtering**: Automatically processes only relevant code files
- **Interactive CLI**: Easy-to-use command-line interface
- **Batch Operations**: Store and search multiple repositories

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (for embeddings and LLM)
- Supabase account and database

*Note*🚩: I used Qwen-3-coder as the llm but you can use any llm of your choice, check the workflow\nodes.py to LLM assignment. 

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd repository-search-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Set up Supabase database:
   - Run the SQL commands in `supabase_schema.sql` in your Supabase SQL editor
   - This creates the necessary tables and functions

### Usage

#### Store a Repository

Store a GitHub repository:
```bash
python store_repos.py
```

Store a custom repository interactively:
```bash
python store_repos.py --custom
```

#### Search Repositories

Interactive search:
```bash
python search_repos.py --interactive
```

Search all repositories:
```bash
python search_repos.py --all "authentication logic"
```

Run example searches:
```bash
python search_repos.py
```

#### Run AI-Powered PR Analysis

Execute the agentic workflow for PR analysis:
```bash
python examples/pr_analysis_workflow_demo.py
```

Test the agentic workflow components:
```bash
python examples/test_agentic_workflow.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI API Key for embeddings
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Database URL
SUPABASE_DB_URL=postgresql://user:password@host:port/database

# Optional: Azure DevOps Personal Access Token
AZURE_API_KEY=your_azure_pat_here
```

### Supported File Types

The system automatically processes these file types:
- **Code**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`
- **Web**: `.html`, `.css`, `.scss`, `.jsx`, `.tsx`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `.sql`
- **Documentation**: `.md`, `.txt`, `.rst`
- **Special files**: `README`, `LICENSE`, `Dockerfile`, `requirements.txt`, etc.

## API Reference

### Core Functions

#### `store_repos.py`

```python
# Store GitHub repository
store_github_repo(github_url, branch=None, refresh=False)

# Store Azure DevOps repository  
store_azure_repo(organization, project, repository, branch=None, pat=None, refresh=False)
```

#### `search_repos.py`

```python
# Search specific repository
search_repository(repo_name, query, limit=5, show_content=False)

# Search all repositories
search_all_repos(query, limit=3)

# Interactive search interface
interactive_search()
```

### Utility Functions

#### `utils/git_utils.py`

```python
# Get repository information from GitHub
get_github_repo_info(github_url, branch=None)

# Get repository information from Azure DevOps
get_azure_repo_info(organization, project, repository, branch=None, pat=None)
```

#### `utils/vector_utils.py`

```python
# Store repository in vector database
store_repo_in_own_collection(repo_info, refresh=False)

# Search within repository collection
search_repo_collection(repo_name, query, limit=5)

# List all repository collections
list_repo_collections()
```

## Examples

### Store Multiple Repositories

```python
# GitHub repository
store_github_repo("https://github.com/user/repo", branch="main")

# Azure DevOps repository
store_azure_repo("org", "project", "repo", branch="develop")
```

### Search Examples

```python
# Find authentication code
search_repository("my-repo", "user authentication and login")

# Find database queries
search_repository("my-repo", "SQL queries and database connections")

# Find API endpoints
search_repository("my-repo", "REST API endpoints and routes")
```

### AI-Powered PR Analysis Examples

```python
# Run the complete agentic workflow for PR analysis
from workflow.graph import create_default_workflow
from workflow.state import WorkflowState

# Create workflow
workflow = create_default_workflow()

# Create initial state with PR data
state = WorkflowState(collection_name="repo-name", pr_data=json_pr_data)

# Execute workflow
result = workflow.invoke(state)
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Git Repos     │───▶│   Processing     │───▶│   Supabase      │
│ (GitHub/Azure)  │    │   & Embedding    │    │  Vector Store   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   File Filter    │    │   Search API    │
                       │   & Content      │    │   & Results     │
                       └──────────────────┘    └─────────────────┘
```

## Agentic Workflow

The system implements an AI-powered agentic workflow for Pull Request (PR) analysis using LangGraph. This workflow consists of specialized agents that collaborate to analyze code changes and provide comprehensive feedback.

### Workflow Components

1. **Parsing Function** (`parse_pr_data`): Extracts repository information and collection name from PR data
2. **Analysis Agent** (`pr_analysis_agent`): Reviews code changes for correctness, style, maintainability, and security risks
3. **Tools**: Vector database query tools that allow agents to explore the repository context

### Agent Capabilities

The PR Analysis Agent has access to the following tools:
- `list_directories`: List all file paths in the repository
- `get_metadata_by_id`: Inspect metadata for a file without reading its full content
- `get_content_by_id`: Fetch the actual code of a file for deeper analysis
- `search_vector_database`: Search semantically for related files or concepts in the repo

### Workflow Execution

The agentic workflow follows this sequence:
1. Parse PR data to extract repository information
2. Analyze code changes using the AI agent with access to repository tools
3. Generate structured feedback including:
   - Summary of the PR
   - Detailed findings for each file
   - Security concerns
   - Final recommendation

### State Management

The workflow maintains state throughout execution using the `WorkflowState` dataclass, which tracks:
- Collection name and PR data
- Completed workflow nodes
- Analysis results and metadata
- Execution timing information

## Troubleshooting

### Common Issues

1. **"No collections found"**: Run `store_repos.py` first to add repositories
2. **Authentication errors**: Check your API keys in `.env` file
3. **Database connection**: Verify your `SUPABASE_DB_URL` is correct
4. **Large repositories**: The system skips files >100KB automatically

### Performance Tips

- Use specific queries for better results
- Limit search results for faster responses
- Refresh collections only when necessary
- Monitor your OpenAI API usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
