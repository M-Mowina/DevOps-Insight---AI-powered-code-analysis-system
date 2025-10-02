"""
Vector utilities for structured repository data.
Handles storage and retrieval of structured chunks with symbol information.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import vecs
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()


class StructuredVectorStore:
    """Vector store optimized for structured repository chunks."""
    
    def __init__(self, supabase_url: Optional[str] = None, embedding_model: str = "text-embedding-3-small"):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_DB_URL")
        if not self.supabase_url:
            raise ValueError("SUPABASE_DB_URL environment variable not set")
        
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.dimension = 1536  # OpenAI text-embedding-3-small dimension
        
    def create_collection(self, collection_name: str, drop_if_exists: bool = False) -> Any:
        """Create or get a vector collection."""
        vx = vecs.create_client(self.supabase_url)
        
        try:
            if drop_if_exists:
                try:
                    vx.delete_collection(collection_name)
                    print(f"🗑️  Deleted existing collection: {collection_name}")
                except Exception:
                    pass  # Collection might not exist
            
            collection = vx.get_or_create_collection(
                name=collection_name,
                dimension=self.dimension
            )
            
            print(f"✅ Collection ready: {collection_name}")
            return collection
            
        finally:
            vx.disconnect()
    
    def store_structured_repo(self, repo_data: Dict[str, Any], refresh: bool = False) -> str:
        """
        Store structured repository data in vector database.
        
        Args:
            repo_data (Dict[str, Any]): Structured repository data
            refresh (bool): Whether to refresh existing collection
            
        Returns:
            str: Collection name
        """
        repo_name = repo_data['repo_name']
        collection_name = repo_name  # Use simple repo name like old version
        
        print(f"📥 Storing structured repo: {repo_name}")
        print(f"📊 Chunks to store: {len(repo_data['files'])}")
        
        # Create collection
        collection = self.create_collection(collection_name, drop_if_exists=refresh)
        
        # Prepare vectors for upsert
        vectors_to_upsert = []
        
        for file_chunk in repo_data['files']:
            try:
                # Generate embedding for chunk content
                embedding = self.embeddings.embed_query(file_chunk['content'])
                
                # Store the embedding in the chunk data
                file_chunk['embedding'] = embedding
                
                # Create the structured record matching your schema
                structured_record = {
                    'id': file_chunk['id'],  # File path (with #chunk_X if chunked)
                    'repo_id': file_chunk['repo_id'],  # Repository name
                    'chunk_id': file_chunk['chunk_id'],  # Chunk number or None
                    'content': file_chunk['content'],  # Raw code text
                    'embedding': embedding,  # Vector representation (already a list)
                    'symbols': file_chunk['symbols'],  # Extracted symbols dict
                    'imports': file_chunk['imports'],  # Import statements list
                    'metadata': file_chunk['metadata']  # Language, size, timestamps
                }
                
                # Add source-specific metadata
                if repo_data.get('source_type') == 'github':
                    structured_record['metadata']['source_url'] = repo_data.get('source_url', '')
                elif repo_data.get('source_type') == 'azure_devops':
                    structured_record['metadata']['organization'] = repo_data.get('organization', '')
                    structured_record['metadata']['project'] = repo_data.get('project', '')
                
                # For vector storage, we still need the 3-field format but with all data in metadata
                metadata_for_storage = {
                    'repo_id': file_chunk['repo_id'],
                    'chunk_id': file_chunk['chunk_id'],
                    'content': file_chunk['content'],
                    'symbols': json.dumps(file_chunk['symbols']),
                    'imports': json.dumps(file_chunk['imports']),
                    'metadata': json.dumps(file_chunk['metadata']),
                    'repo_name': repo_data['repo_name'],
                    'path': file_chunk['id']  # Store the full ID as path
                }
                
                # Use chunk ID as vector ID
                vectors_to_upsert.append((file_chunk['id'], embedding, metadata_for_storage))
                
            except Exception as e:
                print(f"⚠️  Error processing chunk {file_chunk['id']}: {e}")
                continue
        
        # Upsert vectors
        if vectors_to_upsert:
            vx = vecs.create_client(self.supabase_url)
            try:
                collection = vx.get_collection(collection_name)
                collection.upsert(vectors_to_upsert)
                print(f"✅ Stored {len(vectors_to_upsert)} chunks in collection: {collection_name}")
            finally:
                vx.disconnect()
        else:
            print("❌ No chunks to store")
        
        return collection_name
    
    def search_structured_repo(self, collection_name: str, query: str, 
                              limit: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search structured repository with optional filters.
        
        Args:
            collection_name (str): Collection name
            query (str): Search query
            limit (int): Maximum results
            filters (Optional[Dict]): Metadata filters
            
        Returns:
            List[Dict]: Search results with structured data
        """
        vx = vecs.create_client(self.supabase_url)
        
        try:
            collection = vx.get_collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Perform search
            results = collection.query(
                data=query_embedding,
                limit=limit,
                include_value=True,
                include_metadata=True,
                filters=filters
            )
            
            # Process results to match your schema
            structured_results = []
            for result in results:
                if len(result) >= 3:
                    file_id = result[0]  # This is the file path (with #chunk_X if chunked)
                    cosine_distance = result[1]  # Distance from vector search
                    similarity_score = 1 - cosine_distance  # Convert distance to similarity
                    stored_metadata = result[2]
                    
                    # Deserialize the stored data
                    symbols = json.loads(stored_metadata.get('symbols', '{}'))
                    imports = json.loads(stored_metadata.get('imports', '[]'))
                    file_metadata = json.loads(stored_metadata.get('metadata', '{}'))
                    
                    # Return in your exact schema format
                    structured_result = {
                        'id': file_id,  # File path (same as old unstructured)
                        'repo_id': stored_metadata.get('repo_id', ''),
                        'chunk_id': stored_metadata.get('chunk_id'),
                        'content': stored_metadata.get('content', ''),
                        'embedding': None,  # Don't return the full vector in search results
                        'symbols': symbols,
                        'imports': imports,
                        'metadata': file_metadata,
                        'similarity_score': similarity_score  # Add for search results
                    }
                    
                    structured_results.append(structured_result)
            
            return structured_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
        finally:
            vx.disconnect()
    
    def search_by_symbols(self, collection_name: str, symbol_type: str, 
                         symbol_name: str, limit: int = 10) -> List[Dict]:
        """
        Search for chunks containing specific symbols.
        
        Args:
            collection_name (str): Collection name
            symbol_type (str): Type of symbol (functions, classes, etc.)
            symbol_name (str): Name of the symbol
            limit (int): Maximum results
            
        Returns:
            List[Dict]: Chunks containing the symbol
        """
        # Use semantic search with symbol-focused query
        query = f"{symbol_type} {symbol_name}"
        results = self.search_structured_repo(collection_name, query, limit)
        
        # Filter results that actually contain the symbol
        filtered_results = []
        for result in results:
            symbols = result.get('symbols', {})
            if symbol_type in symbols and symbol_name in symbols[symbol_type]:
                result['match_type'] = 'exact_symbol'
                filtered_results.append(result)
            elif any(symbol_name.lower() in str(v).lower() for v in symbols.values()):
                result['match_type'] = 'partial_symbol'
                filtered_results.append(result)
        
        return filtered_results
    
    def search_by_imports(self, collection_name: str, import_pattern: str, 
                         limit: int = 10) -> List[Dict]:
        """
        Search for chunks with specific import patterns.
        
        Args:
            collection_name (str): Collection name
            import_pattern (str): Import pattern to search for
            limit (int): Maximum results
            
        Returns:
            List[Dict]: Chunks with matching imports
        """
        query = f"import {import_pattern}"
        results = self.search_structured_repo(collection_name, query, limit)
        
        # Filter by actual imports
        filtered_results = []
        for result in results:
            imports = result.get('imports', [])
            if any(import_pattern.lower() in imp.lower() for imp in imports):
                result['match_type'] = 'import_match'
                filtered_results.append(result)
        
        return filtered_results
    
    def get_repository_overview(self, collection_name: str) -> Dict[str, Any]:
        """
        Get overview statistics for a repository collection.
        
        Args:
            collection_name (str): Collection name
            
        Returns:
            Dict[str, Any]: Repository overview
        """
        vx = vecs.create_client(self.supabase_url)
        
        try:
            collection = vx.get_collection(collection_name)
            
            # Get a sample of chunks to analyze
            dummy_embedding = [0.0] * self.dimension
            sample_results = collection.query(
                data=dummy_embedding,
                limit=100,
                include_metadata=True
            )
            
            if not sample_results:
                return {'error': 'No data found in collection'}
            
            # Analyze the sample
            languages = {}
            file_types = {}
            total_symbols = 0
            total_imports = 0
            chunked_files = 0
            unique_files = set()
            
            for result in sample_results:
                if len(result) >= 3:
                    metadata = result[2]
                    
                    # Language stats
                    lang = metadata.get('language', 'unknown')
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    # File type stats
                    ext = metadata.get('file_extension', 'unknown')
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # Symbol and import stats
                    total_symbols += metadata.get('symbol_count', 0)
                    total_imports += metadata.get('import_count', 0)
                    
                    # Chunking stats
                    if metadata.get('is_chunked', False):
                        chunked_files += 1
                    
                    # Unique files
                    unique_files.add(metadata.get('file_path', ''))
            
            overview = {
                'collection_name': collection_name,
                'total_chunks': len(sample_results),
                'unique_files': len(unique_files),
                'chunked_files': chunked_files,
                'languages': languages,
                'file_types': file_types,
                'total_symbols': total_symbols,
                'total_imports': total_imports,
                'avg_symbols_per_chunk': total_symbols / len(sample_results) if sample_results else 0,
                'avg_imports_per_chunk': total_imports / len(sample_results) if sample_results else 0
            }
            
            return overview
            
        except Exception as e:
            return {'error': str(e)}
        finally:
            vx.disconnect()
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        vx = vecs.create_client(self.supabase_url)
        
        try:
            collections = vx.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
        finally:
            vx.disconnect()
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        vx = vecs.create_client(self.supabase_url)
        
        try:
            vx.delete_collection(collection_name)
            print(f"🗑️  Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
        finally:
            vx.disconnect()


# Convenience functions
def store_structured_repository(repo_data: Dict[str, Any], refresh: bool = False) -> str:
    """
    Convenience function to store structured repository data.
    
    Args:
        repo_data (Dict[str, Any]): Structured repository data
        refresh (bool): Whether to refresh existing collection
        
    Returns:
        str: Collection name
    """
    store = StructuredVectorStore()
    return store.store_structured_repo(repo_data, refresh)


def search_structured_repository(collection_name: str, query: str, limit: int = 5) -> List[Dict]:
    """
    Convenience function to search structured repository.
    
    Args:
        collection_name (str): Collection name
        query (str): Search query
        limit (int): Maximum results
        
    Returns:
        List[Dict]: Search results
    """
    store = StructuredVectorStore()
    return store.search_structured_repo(collection_name, query, limit)


def get_structured_collections() -> List[str]:
    """Get list of structured collections."""
    store = StructuredVectorStore()
    return store.list_collections()


# Aliases for backward compatibility
def store_repo_in_own_collection(repo_data: Dict[str, Any], refresh: bool = False) -> str:
    """Alias for backward compatibility."""
    return store_structured_repository(repo_data, refresh)

def search_repo_collection(collection_name: str, query: str, limit: int = 5) -> List[Dict]:
    """Alias for backward compatibility."""
    return search_structured_repository(collection_name, query, limit)

def list_repo_collections() -> List[str]:
    """Alias for backward compatibility."""
    return get_structured_collections()

def get_vector_client():
    """Get vector client for backward compatibility."""
    try:
        store = StructuredVectorStore()
        return store
    except Exception as e:
        print(f"Error creating vector client: {e}")
        return None

def get_embedding_model():
    """Get embedding model for backward compatibility."""
    try:
        store = StructuredVectorStore()
        return store.embeddings
    except Exception as e:
        print(f"Error creating embedding model: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    print("🔍 Testing Structured Vector Store")
    print("=" * 50)
    
    # Test with sample data
    sample_repo_data = {
        'repo_id': 'test_repo_123',
        'repo_name': 'test-repository',
        'source_type': 'github',
        'source_url': 'https://github.com/test/repo',
        'branches': ['main', 'develop'],
        'commit_count': 100,
        'chunks': [
            {
                'id': 'chunk_123',
                'repo_id': 'test_repo_123',
                'file_path': 'src/main.py',
                'chunk_id': 0,
                'total_chunks': 1,
                'content': 'import os\n\ndef main():\n    print("Hello World")\n\nif __name__ == "__main__":\n    main()',
                'symbols': {
                    'functions': ['main'],
                    'variables': []
                },
                'imports': ['import os'],
                'metadata': {
                    'language': 'python',
                    'file_size': 100,
                    'chunk_size': 100,
                    'is_chunked': False,
                    'file_extension': '.py',
                    'timestamp': '2024-01-15T10:00:00'
                }
            }
        ]
    }
    
    try:
        # Test storage
        store = StructuredVectorStore()
        collection_name = store.store_structured_repo(sample_repo_data, refresh=True)
        
        # Test search
        results = store.search_structured_repo(collection_name, "main function", limit=3)
        print(f"\n🔍 Search results: {len(results)}")
        
        for result in results:
            print(f"   File: {result['file_path']}")
            print(f"   Similarity: {result['similarity_score']:.3f}")
            print(f"   Symbols: {result['symbols']}")
        
        # Test overview
        overview = store.get_repository_overview(collection_name)
        print(f"\n📊 Repository overview:")
        print(f"   Total chunks: {overview.get('total_chunks', 0)}")
        print(f"   Languages: {overview.get('languages', {})}")
        print(f"   Total symbols: {overview.get('total_symbols', 0)}")
        
        print("\n✅ Testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()