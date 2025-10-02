"""
Analysis tools for the code analysis agent system.

This module provides vector database query tools for the LangGraph agents.
The agents will use these tools to gather information and perform their own analysis.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

# Import the existing vector store
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.vector_utils import StructuredVectorStore


# ============================================================================
# VECTOR DATABASE QUERY TOOLS
# ============================================================================

@tool
def list_directories(collection_name: str) -> List[str]:
    """
    List all unique directories/file paths (chunk_ids) in the collection.
    
    Args:
        collection_name: Name of the repository collection
        
    Returns:
        List of chunk IDs (file paths/directories)
    """
    try:
        vector_store = StructuredVectorStore()
        
        # Get a large sample to find all unique directories
        results = vector_store.search_structured_repo(collection_name, "code", limit=1000)
        
        # Extract unique chunk IDs (which are file paths)
        chunk_ids = set()
        for result in results:
            chunk_id = result.get('id', '')
            if chunk_id:
                chunk_ids.add(chunk_id)
        
        return sorted(list(chunk_ids))
        
    except Exception as e:
        return [f'Error listing directories: {str(e)}']


@tool
def get_metadata_by_id(collection_name: str, chunk_id: str) -> Dict[str, Any]:
    """
    Get metadata of a chunk by its ID (excluding content).
    
    Args:
        collection_name: Name of the repository collection
        chunk_id: The chunk ID (file path) to get metadata for
        
    Returns:
        Dictionary containing chunk metadata without content
    """
    try:
        vector_store = StructuredVectorStore()
        
        # Search for the specific chunk ID
        results = vector_store.search_structured_repo(collection_name, chunk_id, limit=10)
        
        # Find exact match
        for result in results:
            if result.get('id') == chunk_id:
                # Return metadata without content
                metadata = {
                    'id': result.get('id'),
                    'repo_id': result.get('repo_id'),
                    'chunk_id': result.get('chunk_id'),
                    'symbols': result.get('symbols', {}),
                    'imports': result.get('imports', []),
                    'metadata': result.get('metadata', {}),
                    'similarity_score': result.get('similarity_score', 0),
                    'tool_used': 'get_metadata_by_id'
                }
                return metadata
        
        return {'error': f'Chunk ID {chunk_id} not found', 'tool_used': 'get_metadata_by_id'}
        
    except Exception as e:
        return {'error': f'Failed to get metadata: {str(e)}', 'tool_used': 'get_metadata_by_id'}


@tool
def get_content_by_id(collection_name: str, chunk_id: str) -> Dict[str, Any]:
    """
    Get the content code of a chunk by its ID.
    
    Args:
        collection_name: Name of the repository collection
        chunk_id: The chunk ID (file path) to get content for
        
    Returns:
        Dictionary containing chunk content
    """
    try:
        vector_store = StructuredVectorStore()
        
        # Search for the specific chunk ID
        results = vector_store.search_structured_repo(collection_name, chunk_id, limit=10)
        
        # Find exact match
        for result in results:
            if result.get('id') == chunk_id:
                return {
                    'id': result.get('id'),
                    'content': result.get('content', ''),
                    'tool_used': 'get_content_by_id'
                }
        
        return {'error': f'Chunk ID {chunk_id} not found', 'tool_used': 'get_content_by_id'}
        
    except Exception as e:
        return {'error': f'Failed to get content: {str(e)}', 'tool_used': 'get_content_by_id'}


@tool
def search_vector_database(collection_name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search the vector database and return top matches with their IDs and metadata.
    
    Args:
        collection_name: Name of the repository collection
        query: Search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching chunks with IDs and metadata (no content)
    """
    try:
        vector_store = StructuredVectorStore()
        results = vector_store.search_structured_repo(collection_name, query, limit)
        
        # Return results with metadata but without content for efficiency
        search_results = []
        for result in results:
            search_result = {
                'id': result.get('id'),
                'repo_id': result.get('repo_id'),
                'chunk_id': result.get('chunk_id'),
                'symbols': result.get('symbols', {}),
                'imports': result.get('imports', []),
                'metadata': result.get('metadata', {}),
                'similarity_score': result.get('similarity_score', 0),
                'tool_used': 'search_vector_database',
                'search_query': query
            }
            search_results.append(search_result)
        
        return search_results
        
    except Exception as e:
        return [{'error': f'Search failed: {str(e)}', 'tool_used': 'search_vector_database'}]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_available_tools() -> List[str]:
    """
    Get list of all available analysis tools.
    
    Returns:
        List of tool names
    """
    return [
        'list_directories',
        'get_metadata_by_id',
        'get_content_by_id',
        'search_vector_database'
    ]


def create_tool_registry() -> Dict[str, Any]:
    """
    Create a registry of all available tools with their metadata.
    
    Returns:
        Dictionary mapping tool names to tool functions
    """
    return {
        'list_directories': list_directories,
        'get_metadata_by_id': get_metadata_by_id,
        'get_content_by_id': get_content_by_id,
        'search_vector_database': search_vector_database
    }