#!/usr/bin/env python3
"""
Storage script for structured repository data with symbcol extraction.
Processes repositories and stores them in vector database with enhanced metadata.
"""

import os
import sys
from dotenv import load_dotenv
from utils.git_utils import (
    get_github_repo_info_structured,
    get_azure_repo_info_structured
)
from utils.vector_utils import (
    StructuredVectorStore,
    store_structured_repository,
    get_structured_collections
)

# Load environment variables
load_dotenv()


def store_github_repo_structured(github_url: str, branch: str = None, refresh: bool = False,
                                chunk_size: int = 4000, chunk_overlap: int = 400) -> bool:
    """
    Clone and store a GitHub repository with structured data and symbol extraction.
    
    Args:
        github_url (str): GitHub repository URL
        branch (str, optional): Specific branch to clone
        refresh (bool): Whether to refresh existing collection
        chunk_size (int): Maximum chunk size in characters
        chunk_overlap (int): Overlap between chunks
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"📥 Processing GitHub repo: {github_url}")
    if branch:
        print(f"🌿 Branch: {branch}")
    print(f"🔧 Chunking: size={chunk_size}, overlap={chunk_overlap}")
    
    # Extract structured repository data
    repo_data = get_github_repo_info_structured(
        github_url, branch, chunk_size, chunk_overlap
    )
    
    if not repo_data:
        print("❌ Failed to extract repository data")
        return False
    
    print(f"📊 Repository processed:")
    print(f"   Name: {repo_data['repo_name']}")
    print(f"   Total chunks: {repo_data['chunking_info']['total_chunks']}")
    print(f"   Files chunked: {repo_data['chunking_info']['files_chunked']}")
    print(f"   Files whole: {repo_data['chunking_info']['files_not_chunked']}")
    
    # Count symbols and imports from files
    total_symbols = sum(sum(len(v) for v in chunk['symbols'].values()) for chunk in repo_data['files'])
    total_imports = sum(len(chunk['imports']) for chunk in repo_data['files'])
    print(f"   Total symbols: {total_symbols}")
    print(f"   Total imports: {total_imports}")
    
    try:
        # Store in vector database
        collection_name = store_structured_repository(repo_data, refresh=refresh)
        print(f"✅ Successfully stored in collection: {collection_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store repository: {e}")
        return False


def store_azure_repo_structured(organization: str, project: str, repository: str,
                               branch: str = None, pat: str = None, refresh: bool = False,
                               chunk_size: int = 4000, chunk_overlap: int = 400) -> bool:
    """
    Clone and store an Azure DevOps repository with structured data and symbol extraction.
    
    Args:
        organization (str): Azure DevOps organization
        project (str): Project name
        repository (str): Repository name
        branch (str, optional): Specific branch to clone
        pat (str, optional): Personal Access Token
        refresh (bool): Whether to refresh existing collection
        chunk_size (int): Maximum chunk size in characters
        chunk_overlap (int): Overlap between chunks
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"📥 Processing Azure DevOps repo: {organization}/{project}/{repository}")
    if branch:
        print(f"🌿 Branch: {branch}")
    print(f"🔧 Chunking: size={chunk_size}, overlap={chunk_overlap}")
    
    # Use PAT from environment if not provided
    if not pat:
        pat = os.getenv("AZURE_API_KEY")
        if not pat:
            print("❌ No Azure PAT provided and AZURE_API_KEY not found in environment")
            return False
    
    # Extract structured repository data
    repo_data = get_azure_repo_info_structured(
        organization, project, repository, pat, branch, chunk_size, chunk_overlap
    )
    
    if not repo_data:
        print("❌ Failed to extract repository data")
        return False
    
    print(f"📊 Repository processed:")
    print(f"   Name: {repo_data['repo_name']}")
    print(f"   Organization: {repo_data.get('organization', 'N/A')}")
    print(f"   Project: {repo_data.get('project', 'N/A')}")
    print(f"   Total chunks: {repo_data['chunking_info']['total_chunks']}")
    print(f"   Files chunked: {repo_data['chunking_info']['files_chunked']}")
    print(f"   Files whole: {repo_data['chunking_info']['files_not_chunked']}")
    
    # Count symbols and imports from files
    total_symbols = sum(sum(len(v) for v in chunk['symbols'].values()) for chunk in repo_data['files'])
    total_imports = sum(len(chunk['imports']) for chunk in repo_data['files'])
    print(f"   Total symbols: {total_symbols}")
    print(f"   Total imports: {total_imports}")
    
    try:
        # Store in vector database
        collection_name = store_structured_repository(repo_data, refresh=refresh)
        print(f"✅ Successfully stored in collection: {collection_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store repository: {e}")
        return False


def list_stored_repositories():
    """List all stored structured repositories."""
    print("📋 Stored Structured Repositories:")
    print("=" * 40)
    
    try:
        collections = get_structured_collections()
        
        if not collections:
            print("   No structured repositories found")
            return
        
        store = StructuredVectorStore()
        
        for i, collection in enumerate(collections, 1):
            print(f"\n{i}. {collection}")
            
            # Get overview
            overview = store.get_repository_overview(collection)
            if 'error' not in overview:
                print(f"   📊 Chunks: {overview.get('total_chunks', 0)}")
                print(f"   📁 Files: {overview.get('unique_files', 0)}")
                print(f"   🔧 Languages: {list(overview.get('languages', {}).keys())}")
                print(f"   🧩 Symbols: {overview.get('total_symbols', 0)}")
                print(f"   📦 Imports: {overview.get('total_imports', 0)}")
            else:
                print(f"   ⚠️  Error getting overview: {overview['error']}")
    
    except Exception as e:
        print(f"❌ Error listing repositories: {e}")


def interactive_storage():
    """Interactive repository storage interface."""
    print("🔧 Interactive Structured Repository Storage")
    print("=" * 50)
    
    # Repository type selection
    repo_type = input("Repository type (github/azure): ").lower().strip()
    
    if repo_type not in ['github', 'azure']:
        print("❌ Invalid repository type")
        return False
    
    # Chunking configuration
    print("\n🔧 Chunking Configuration:")
    chunk_size = input("Chunk size (default 4000): ").strip()
    chunk_size = int(chunk_size) if chunk_size.isdigit() else 4000
    
    chunk_overlap = input("Chunk overlap (default 400): ").strip()
    chunk_overlap = int(chunk_overlap) if chunk_overlap.isdigit() else 400
    
    refresh = input("Refresh existing collection? (y/N): ").lower().startswith('y')
    
    if repo_type == 'github':
        url = input("\nGitHub URL: ").strip()
        branch = input("Branch (optional): ").strip() or None
        
        return store_github_repo_structured(
            url, branch, refresh, chunk_size, chunk_overlap
        )
    
    elif repo_type == 'azure':
        org = input("\nOrganization: ").strip()
        project = input("Project: ").strip()
        repo = input("Repository: ").strip()
        branch = input("Branch (optional): ").strip() or None
        
        return store_azure_repo_structured(
            org, project, repo, branch, None, refresh, chunk_size, chunk_overlap
        )


def main():
    """Main function with example repository configurations."""
    print("🚀 Structured Repository Storage")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("SUPABASE_DB_URL"):
        print("❌ SUPABASE_DB_URL environment variable not set")
        sys.exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # List existing collections
    list_stored_repositories()
    
    print("\n" + "=" * 50)
    
    # Example 1: GitHub Repository
    print("\n1️⃣ Storing GitHub Repository (Structured)")
    github_success = store_github_repo_structured(
        github_url="https://github.com/M-Mowina/LinkedIn-Booster",
        branch=None,
        refresh=True,
        chunk_size=4000,
        chunk_overlap=400
    )
    
    # Example 2: Azure DevOps Repository
    print("\n2️⃣ Storing Azure DevOps Repository (Structured)")
    azure_success = store_azure_repo_structured(
        organization="areebgroup",
        project="Internship-Playground",
        repository="Internship-ai",
        branch="Linked-Booster-LangGraph-Task",
        pat=None,  # Will use AZURE_API_KEY from environment
        refresh=True,
        chunk_size=4000,
        chunk_overlap=400
    )
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   GitHub repo: {'✅ Success' if github_success else '❌ Failed'}")
    print(f"   Azure repo: {'✅ Success' if azure_success else '❌ Failed'}")
    
    if github_success or azure_success:
        print("\n📋 Updated structured repositories:")
        list_stored_repositories()


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_storage()
        elif sys.argv[1] == "--list":
            list_stored_repositories()
        else:
            print("Usage:")
            print("  python store_repos.py                    # Run examples")
            print("  python store_repos.py --interactive      # Interactive mode")
            print("  python store_repos.py --list             # List stored repos")
    else:
        main()