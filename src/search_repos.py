#!/usr/bin/env python3
"""
Search script for structured repository data with symbol-aware queries.
Provides advanced search capabilities including symbol search, import search, and semantic search.
"""

import os
import sys
import json
from dotenv import load_dotenv
from utils.vector_utils import (
    StructuredVectorStore,
    search_structured_repository,
    get_structured_collections
)

# Load environment variables
load_dotenv()


def display_structured_results(results, query, collection_name):
    """
    Display structured search results with enhanced formatting.
    
    Args:
        results (list): Search results
        query (str): Original search query
        collection_name (str): Collection name
    """
    repo_name = collection_name.replace('structured_', '')
    print(f"\n🔍 Search Results for: '{query}' in '{repo_name}'")
    print("=" * 80)
    
    if not results:
        print("❌ No results found")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 📄 {result['id']}")  # Use 'id' instead of 'file_path'
        print(f"   🎯 Similarity: {result['similarity_score']:.4f}")
        
        # Get language from metadata
        metadata = result.get('metadata', {})
        language = metadata.get('language', 'unknown')
        print(f"   🔧 Language: {language}")
        
        # Chunk information
        if result.get('chunk_id') is not None:
            total_chunks = metadata.get('total_chunks', 1)
            print(f"   📄 Chunk: {result['chunk_id'] + 1}/{total_chunks}")
        
        # Symbol information
        symbols = result.get('symbols', {})
        if symbols:
            symbol_summary = []
            for symbol_type, symbol_list in symbols.items():
                if symbol_list:
                    count = len(symbol_list)
                    preview = symbol_list[:3]
                    if count > 3:
                        preview_str = f"{', '.join(preview)}... (+{count-3} more)"
                    else:
                        preview_str = ', '.join(preview)
                    symbol_summary.append(f"{symbol_type}: {preview_str}")
            
            if symbol_summary:
                print(f"   🧩 Symbols: {' | '.join(symbol_summary)}")
        
        # Import information
        imports = result.get('imports', [])
        if imports:
            import_preview = imports[:3]
            if len(imports) > 3:
                import_str = f"{', '.join(import_preview)}... (+{len(imports)-3} more)"
            else:
                import_str = ', '.join(import_preview)
            print(f"   📦 Imports: {import_str}")
        
        # Metadata
        print(f"   📊 Size: {metadata.get('size', 0)} chars")
        print(f"   🏷️  Symbols: {len(symbols)}, Imports: {len(imports)}")
        
        # Match type (if available)
        if 'match_type' in result:
            print(f"   🎯 Match: {result['match_type']}")
        
        print("-" * 60)


def semantic_search(collection_name: str, query: str, limit: int = 5, show_content: bool = False):
    """
    Perform semantic search on structured repository.
    
    Args:
        collection_name (str): Collection name
        query (str): Search query
        limit (int): Maximum results
        show_content (bool): Whether to show content
        
    Returns:
        list: Search results
    """
    print(f"🔍 Semantic search in: {collection_name}")
    print(f"📝 Query: {query}")
    
    store = StructuredVectorStore()
    results = store.search_structured_repo(collection_name, query, limit)
    
    display_structured_results(results, query, collection_name)
    
    if show_content and results:
        print(f"\n📖 Content Preview:")
        print("=" * 80)
        
        for i, result in enumerate(results[:3], 1):  # Show content for top 3 results
            print(f"\n{i}. 📄 {result['id']}")  # Use 'id' instead of 'file_path'
            print(f"   🎯 Similarity: {result['similarity_score']:.4f}")
            
            content = result.get('content', '')
            if content:
                # Show first 300 characters
                preview = content[:300]
                if len(content) > 300:
                    preview += "..."
                
                print(f"   📝 Content:")
                print("   " + "─" * 60)
                for line_num, line in enumerate(preview.split('\n')[:10], 1):
                    print(f"   {line_num:3d} | {line}")
                print("   " + "─" * 60)
            else:
                print("   📝 No content available")
    
    return results


def symbol_search(collection_name: str, symbol_type: str, symbol_name: str, limit: int = 10):
    """
    Search for specific symbols in the repository.
    
    Args:
        collection_name (str): Collection name
        symbol_type (str): Type of symbol (functions, classes, etc.)
        symbol_name (str): Name of the symbol
        limit (int): Maximum results
        
    Returns:
        list: Search results
    """
    print(f"🧩 Symbol search in: {collection_name}")
    print(f"🔍 Looking for {symbol_type}: {symbol_name}")
    
    store = StructuredVectorStore()
    results = store.search_by_symbols(collection_name, symbol_type, symbol_name, limit)
    
    if results:
        print(f"\n✅ Found {len(results)} chunks containing '{symbol_name}'")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result['id']}")  # Use 'id' instead of 'file_path'
            print(f"   🎯 Similarity: {result['similarity_score']:.4f}")
            print(f"   🏷️  Match: {result.get('match_type', 'unknown')}")
            
            # Show the specific symbols found
            symbols = result.get('symbols', {})
            if symbol_type in symbols and symbol_name in symbols[symbol_type]:
                print(f"   ✅ Exact match in {symbol_type}")
            
            # Show all symbols of this type
            if symbol_type in symbols:
                related_symbols = [s for s in symbols[symbol_type] if symbol_name.lower() in s.lower()]
                if related_symbols:
                    print(f"   🔗 Related {symbol_type}: {', '.join(related_symbols[:5])}")
    else:
        print(f"❌ No chunks found containing '{symbol_name}' in {symbol_type}")
    
    return results


def import_search(collection_name: str, import_pattern: str, limit: int = 10):
    """
    Search for specific import patterns.
    
    Args:
        collection_name (str): Collection name
        import_pattern (str): Import pattern to search for
        limit (int): Maximum results
        
    Returns:
        list: Search results
    """
    print(f"📦 Import search in: {collection_name}")
    print(f"🔍 Looking for imports containing: {import_pattern}")
    
    store = StructuredVectorStore()
    results = store.search_by_imports(collection_name, import_pattern, limit)
    
    if results:
        print(f"\n✅ Found {len(results)} chunks with matching imports")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result['id']}")  # Use 'id' instead of 'file_path'
            print(f"   🎯 Similarity: {result['similarity_score']:.4f}")
            
            # Show matching imports
            imports = result.get('imports', [])
            matching_imports = [imp for imp in imports if import_pattern.lower() in imp.lower()]
            
            if matching_imports:
                print(f"   📦 Matching imports:")
                for imp in matching_imports[:5]:
                    print(f"      • {imp}")
                
                if len(matching_imports) > 5:
                    print(f"      ... and {len(matching_imports) - 5} more")
    else:
        print(f"❌ No chunks found with imports containing '{import_pattern}'")
    
    return results


def repository_overview(collection_name: str):
    """
    Show overview of a structured repository.
    
    Args:
        collection_name (str): Collection name
    """
    repo_name = collection_name.replace('structured_', '')
    print(f"📊 Repository Overview: {repo_name}")
    print("=" * 50)
    
    store = StructuredVectorStore()
    overview = store.get_repository_overview(collection_name)
    
    if 'error' in overview:
        print(f"❌ Error: {overview['error']}")
        return
    
    print(f"📄 Total chunks: {overview.get('total_chunks', 0)}")
    print(f"📁 Unique files: {overview.get('unique_files', 0)}")
    print(f"🔧 Chunked files: {overview.get('chunked_files', 0)}")
    
    # Language breakdown
    languages = overview.get('languages', {})
    if languages:
        print(f"\n🔧 Languages:")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            print(f"   {lang}: {count} chunks")
    
    # File type breakdown
    file_types = overview.get('file_types', {})
    if file_types:
        print(f"\n📄 File types:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {ext}: {count} chunks")
    
    # Symbol statistics
    print(f"\n🧩 Symbol statistics:")
    print(f"   Total symbols: {overview.get('total_symbols', 0)}")
    print(f"   Avg per chunk: {overview.get('avg_symbols_per_chunk', 0):.1f}")
    
    print(f"\n📦 Import statistics:")
    print(f"   Total imports: {overview.get('total_imports', 0)}")
    print(f"   Avg per chunk: {overview.get('avg_imports_per_chunk', 0):.1f}")


def interactive_search():
    """Interactive search interface for structured repositories."""
    print("🔍 Interactive Structured Repository Search")
    print("=" * 60)
    
    # List available collections
    collections = get_structured_collections()
    
    if not collections:
        print("❌ No structured repositories found")
        print("💡 Run store_repos_structured.py first to add repositories")
        return
    
    print("\n📋 Available structured repositories:")
    for i, collection in enumerate(collections, 1):
        repo_name = collection.replace('structured_', '')
        print(f"   {i}. {repo_name}")
    
    # Repository selection
    while True:
        try:
            choice = input(f"\nSelect repository (1-{len(collections)}): ").strip()
            repo_index = int(choice) - 1
            
            if 0 <= repo_index < len(collections):
                selected_collection = collections[repo_index]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(collections)}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    repo_name = selected_collection.replace('structured_', '')
    print(f"\n✅ Selected: {repo_name}")
    
    # Search type selection
    print(f"\n🔍 Search options:")
    print("1. Semantic search (natural language)")
    print("2. Symbol search (functions, classes, etc.)")
    print("3. Import search (dependencies)")
    print("4. Repository overview")
    
    search_type = input("\nSelect search type (1-4): ").strip()
    
    if search_type == "1":
        # Semantic search
        query = input("\n🔍 Enter search query: ").strip()
        if not query:
            print("❌ Query cannot be empty")
            return
        
        limit = int(input("📊 Number of results (default 5): ").strip() or "5")
        show_content = input("📖 Show content preview? (y/N): ").lower().startswith('y')
        
        semantic_search(selected_collection, query, limit, show_content)
    
    elif search_type == "2":
        # Symbol search
        print("\n🧩 Symbol types: functions, classes, variables, types, modules")
        symbol_type = input("Symbol type: ").strip().lower()
        symbol_name = input("Symbol name: ").strip()
        
        if not symbol_type or not symbol_name:
            print("❌ Both symbol type and name are required")
            return
        
        limit = int(input("📊 Number of results (default 10): ").strip() or "10")
        symbol_search(selected_collection, symbol_type, symbol_name, limit)
    
    elif search_type == "3":
        # Import search
        import_pattern = input("\n📦 Import pattern to search for: ").strip()
        if not import_pattern:
            print("❌ Import pattern cannot be empty")
            return
        
        limit = int(input("📊 Number of results (default 10): ").strip() or "10")
        import_search(selected_collection, import_pattern, limit)
    
    elif search_type == "4":
        # Repository overview
        repository_overview(selected_collection)
    
    else:
        print("❌ Invalid search type")
        return
    
    # Ask if user wants to search again
    if input("\n🔄 Search again? (y/N): ").lower().startswith('y'):
        interactive_search()


def main():
    """Main function with example searches."""
    print("🔍 Structured Repository Search Tool")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("SUPABASE_DB_URL"):
        print("❌ SUPABASE_DB_URL environment variable not set")
        sys.exit(1)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    # List available repositories
    collections = get_structured_collections()
    
    if not collections:
        print("❌ No structured repositories found")
        print("💡 Run store_repos_structured.py first to add repositories")
        return
    
    print(f"\n📋 Found {len(collections)} structured repositories:")
    for i, collection in enumerate(collections, 1):
        repo_name = collection.replace('structured_', '')
        print(f"   {i}. {repo_name}")
    
    # Example searches with first repository
    if collections:
        example_collection = collections[0]
        repo_name = example_collection.replace('structured_', '')
        
        print(f"\n🔍 Example searches in '{repo_name}':")
        
        # Example 1: Semantic search
        print(f"\n1️⃣ Semantic Search:")
        semantic_search(example_collection, "main function workflow", limit=3)
        
        # Example 2: Symbol search
        print(f"\n2️⃣ Symbol Search:")
        symbol_search(example_collection, "functions", "main", limit=3)
        
        # Example 3: Import search
        print(f"\n3️⃣ Import Search:")
        import_search(example_collection, "os", limit=3)
        
        # Example 4: Repository overview
        print(f"\n4️⃣ Repository Overview:")
        repository_overview(example_collection)


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_search()
        else:
            print("Usage:")
            print("  python search_repos.py                    # Run examples")
            print("  python search_repos.py --interactive      # Interactive mode")
    else:
        main()