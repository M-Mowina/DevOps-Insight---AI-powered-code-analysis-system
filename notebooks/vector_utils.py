import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import vecs
import json

# Load environment variables
load_dotenv()


def get_embedding_model():
    """Initialize and return the OpenAI embedding model."""
    return OpenAIEmbeddings(model="text-embedding-3-small")


def get_vector_client():
    """Initialize and return the Supabase vector client."""
    supabase_db_url = os.getenv("SUPABASE_DB_URL")
    if not supabase_db_url:
        raise ValueError("SUPABASE_DB_URL environment variable not set")
    return vecs.create_client(supabase_db_url)


def store_repo_in_own_collection(repo_info, refresh=False):
    """
    Store repository information in a dedicated vector collection.
    
    Args:
        repo_info (dict): Repository information containing files and metadata
        refresh (bool): Whether to delete existing collection before creating new one
    
    Returns:
        str: Name of the collection created
    """
    repo_name = repo_info['repo_name']
    
    # Initialize clients
    vx = get_vector_client()
    embeddings = get_embedding_model()
    
    if refresh:
        # Drop existing collection if it exists
        try:
            vx.delete_collection(repo_name)
            print(f"🗑️ Old collection '{repo_name}' deleted.")
        except Exception:
            pass  # collection may not exist yet
    
    # Create/get a dedicated collection for this repo
    collection = vx.get_or_create_collection(name=repo_name, dimension=1536)
    
    vectors_to_upsert = []
    
    for file in repo_info['files']:
        content = file['content']
        
        # Generate embedding for file content
        embedding = embeddings.embed_query(content)
        
        # Create unique ID for this file
        unique_id = f"{repo_name}/{file['path']}"
        
        # Prepare metadata (store full content like your working version)
        metadata = {
            'repo_name': repo_name,
            'path': file['path'],
            'content': content,  # Store the full content for retrieval
            'commit_count': repo_info['commit_count'],
            'branches': repo_info['branches']  # List is JSON-serializable, don't stringify
        }
        
        vectors_to_upsert.append((unique_id, embedding, metadata))
    
    # Upsert all vectors at once
    collection.upsert(vectors_to_upsert)
    
    print(f"✅ Stored {len(vectors_to_upsert)} files into collection '{repo_name}'")
    return repo_name


def search_repo_collection(repo_name, query, limit=5):
    """
    Search within a specific repository collection.
    
    Args:
        repo_name (str): Name of the repository collection
        query (str): Search query
        limit (int): Maximum number of results to return
    
    Returns:
        list: Search results with metadata
    """
    vx = get_vector_client()
    embeddings = get_embedding_model()
    
    try:
        collection = vx.get_collection(name=repo_name)
        query_embedding = embeddings.embed_query(query)
        
        # Query the collection
        results = collection.query(
            data=query_embedding,
            limit=limit,
            include_metadata=True,
            include_value=True
        )
        
        # Convert results to a more usable format
        # vecs returns SQLAlchemy Row objects with: (id, metadata)
        formatted_results = []
        for i, result in enumerate(results):
            formatted_result = {
                'id': result[0] if len(result) > 0 else None,
                'cos_distance': result[1],
                'metadata': result[2] if len(result) > 1 else {}
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
        
    except Exception as e:
        print(f"Error searching collection '{repo_name}': {e}")
        return []


def list_repo_collections():
    """
    List all available repository collections.
    
    Returns:
        list: Names of all collections
    """
    vx = get_vector_client()
    try:
        collections = vx.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        print(f"Error listing collections: {e}")
        return []


def delete_repo_collection(repo_name):
    """
    Delete a repository collection.
    
    Args:
        repo_name (str): Name of the repository collection to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    vx = get_vector_client()
    try:
        vx.delete_collection(repo_name)
        print(f"🗑️ Collection '{repo_name}' deleted successfully.")
        return True
    except Exception as e:
        print(f"Error deleting collection '{repo_name}': {e}")
        return False


# Example usage
if __name__ == "__main__":
    # This would typically be called with repo_info from git_utils
    # store_repo_in_own_collection(repo_info)
    pass

def debug_search_results(repo_name, query, limit=2):
    """
    Debug function to inspect the raw search results format.
    
    Args:
        repo_name (str): Name of the repository collection
        query (str): Search query
        limit (int): Maximum number of results to return
    """
    vx = get_vector_client()
    embeddings = get_embedding_model()
    
    try:
        collection = vx.get_collection(name=repo_name)
        query_embedding = embeddings.embed_query(query)
        
        print(f"🔍 Debug search in '{repo_name}' for query: '{query}'")
        
        # Query the collection
        raw_results = collection.query(
            data=query_embedding,
            limit=limit,
            include_metadata=True
        )
        
        print(f"📊 Raw results type: {type(raw_results)}")
        print(f"📊 Raw results length: {len(raw_results) if hasattr(raw_results, '__len__') else 'N/A'}")
        
        if raw_results:
            print(f"📊 First result type: {type(raw_results[0])}")
            print(f"📊 First result: {raw_results[0]}")
            
            if len(raw_results[0]) > 0:
                print(f"📊 First result parts:")
                for i, part in enumerate(raw_results[0]):
                    print(f"   Part {i}: {type(part)} = {part}")
        
        return raw_results
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return None
def get_file_content(repo_name, file_path):
    """
    Get the full content of a specific file from the vector database.
    
    Args:
        repo_name (str): Name of the repository collection
        file_path (str): Path of the file to retrieve
    
    Returns:
        str: File content or None if not found
    """
    vx = get_vector_client()
    
    try:
        collection = vx.get_collection(name=repo_name)
        
        # Search for the specific file by ID
        file_id = f"{repo_name}/{file_path}"
        
        # Use a simple query to find the exact file
        # Since we can't query by ID directly, we'll search and filter
        embeddings = get_embedding_model()
        dummy_query = embeddings.embed_query("content")  # Dummy query
        
        results = collection.query(
            data=dummy_query,
            limit=100,  # Get more results to find our file
            include_metadata=True
        )
        
        # Find the specific file
        for result in results:
            if result[0] == file_id:  # Match the ID
                metadata = result[1] if len(result) > 1 else {}
                return metadata.get('content', '')
        
        return None
        
    except Exception as e:
        print(f"Error retrieving file content: {e}")
        return None


def search_with_content(repo_name, query, limit=5):
    """
    Search and return results with full content included.
    
    Args:
        repo_name (str): Name of the repository collection
        query (str): Search query
        limit (int): Maximum number of results to return
    
    Returns:
        list: Search results with full content
    """
    results = search_repo_collection(repo_name, query, limit)
    
    # Add full content to each result
    for result in results:
        metadata = result.get('metadata', {})
        file_path = metadata.get('path', '')
        
        if file_path:
            full_content = get_file_content(repo_name, file_path)
            if full_content:
                result['full_content'] = full_content
    
    return results