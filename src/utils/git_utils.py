"""
Structured Git utilities with symbol extraction.
Returns repository information in a structured schema optimized for vector storage and code analysis.
"""

from urllib.parse import urlparse
import os
import tempfile
import shutil
import stat
import git
from git import Repo
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from typing import Dict, List, Optional, Any
import hashlib
import time
from datetime import datetime
from .symbol_extractor import extract_file_symbols, create_symbol_summary, symbol_extractor


def generate_unique_id(content: str, prefix: str = "") -> str:
    """Generate a unique ID based on content hash."""
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    return f"{prefix}{content_hash}_{timestamp}" if prefix else f"{content_hash}_{timestamp}"


def get_language_from_extension(file_path: str) -> Optional[Language]:
    """Map file extensions to LangChain Language enum values."""
    ext = os.path.splitext(file_path)[1].lower()
    
    extension_map = {
        '.py': Language.PYTHON,
        '.js': Language.JS,
        '.ts': Language.TS,
        '.jsx': Language.JS,
        '.tsx': Language.TS,
        '.java': Language.JAVA,
        '.kt': Language.KOTLIN,
        '.cpp': Language.CPP,
        '.cc': Language.CPP,
        '.cxx': Language.CPP,
        '.c': Language.C,
        '.h': Language.C,
        '.hpp': Language.CPP,
        '.cs': Language.CSHARP,
        '.php': Language.PHP,
        '.rb': Language.RUBY,
        '.go': Language.GO,
        '.rs': Language.RUST,
        '.swift': Language.SWIFT,
        '.scala': Language.SCALA,
        '.md': Language.MARKDOWN,
        '.html': Language.HTML,
        '.htm': Language.HTML,
        '.sol': Language.SOL,
        '.lua': Language.LUA,
        '.pl': Language.PERL,
        '.hs': Language.HASKELL,
        '.ex': Language.ELIXIR,
        '.exs': Language.ELIXIR,
        '.ps1': Language.POWERSHELL,
        '.vb': Language.VISUALBASIC6,
        '.proto': Language.PROTO,
        '.rst': Language.RST,
        '.tex': Language.LATEX,
        '.cob': Language.COBOL,
        '.cbl': Language.COBOL,
    }
    
    return extension_map.get(ext)


def create_splitter_for_language(language: Language, chunk_size: int = 4000, chunk_overlap: int = 400) -> RecursiveCharacterTextSplitter:
    """Create a language-specific text splitter."""
    return RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )


def extract_imports_from_symbols(symbols: Dict[str, List[str]]) -> List[str]:
    """Extract import statements from symbols dictionary."""
    imports = []
    
    # Different languages use different keys for imports
    import_keys = ['imports', 'includes', 'usings', 'uses', 'requires']
    
    for key in import_keys:
        if key in symbols and symbols[key]:
            imports.extend(symbols[key])
    
    return imports


def extract_symbol_names(symbols: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Extract clean symbol names organized by type."""
    clean_symbols = {}
    
    # Map symbol types to clean names
    symbol_mapping = {
        'functions': ['functions', 'methods'],
        'classes': ['classes', 'structs', 'interfaces', 'traits', 'protocols'],
        'variables': ['variables', 'constants', 'defines'],
        'types': ['types', 'enums', 'typedefs'],
        'modules': ['modules', 'namespaces', 'packages']
    }
    
    for clean_type, symbol_keys in symbol_mapping.items():
        clean_symbols[clean_type] = []
        for key in symbol_keys:
            if key in symbols and symbols[key]:
                clean_symbols[clean_type].extend(symbols[key])
    
    # Remove empty lists
    clean_symbols = {k: v for k, v in clean_symbols.items() if v}
    
    return clean_symbols


def process_file_structured(file_path: str, content: str, repo_id: str, 
                          chunk_size: int = 4000, chunk_overlap: int = 400) -> List[Dict[str, Any]]:
    """
    Process a file and return structured data chunks matching the specified schema.
    
    Args:
        file_path (str): Path to the file
        content (str): File content
        repo_id (str): Repository identifier
        chunk_size (int): Maximum chunk size
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        List[Dict[str, Any]]: List of structured chunk data
    """
    # Extract symbols first
    symbols = extract_file_symbols(file_path, content)
    imports = extract_imports_from_symbols(symbols)
    clean_symbols = extract_symbol_names(symbols)
    
    # Get language info
    language = get_language_from_extension(file_path)
    language_name = language.value if language else 'unknown'
    
    # Determine if we need to chunk
    should_chunk = len(content) > chunk_size and language is not None
    
    if not should_chunk:
        # Single chunk - ID is just the file path
        
        return [{
            'id': file_path,  # Just the file path as ID
            'repo_id': repo_id,
            'chunk_id': None,  # No chunk ID for single files
            'content': content,
            'embedding': None,  # Will be generated during storage
            'symbols': clean_symbols,
            'imports': imports,
            'metadata': {
                'language': language_name,
                'size': len(content),
                'timestamp': datetime.now().isoformat()
            }
        }]
    
    # Multiple chunks
    try:
        splitter = create_splitter_for_language(language, chunk_size, chunk_overlap)
        documents = splitter.create_documents([content])
        
        chunks = []
        
        for i, doc in enumerate(documents):
            chunk_content = doc.page_content
            # ID is file path with chunk suffix
            chunk_id_str = f"{file_path}#chunk_{i}"
            
            chunk_data = {
                'id': chunk_id_str,  # File path with chunk suffix
                'repo_id': repo_id,
                'chunk_id': i,
                'content': chunk_content,
                'embedding': None,  # Will be generated during storage
                'symbols': clean_symbols,  # File-level symbols for context
                'imports': imports,        # File-level imports for context
                'metadata': {
                    'language': language_name,
                    'size': len(chunk_content),
                    'timestamp': datetime.now().isoformat(),
                    'total_chunks': len(documents),
                    'is_chunked': True
                }
            }
            
            chunks.append(chunk_data)
        
        return chunks
        
    except Exception as e:
        # Fallback to single chunk on error
        
        return [{
            'id': file_path,  # Just the file path as ID
            'repo_id': repo_id,
            'chunk_id': None,
            'content': content,
            'embedding': None,
            'symbols': clean_symbols,
            'imports': imports,
            'metadata': {
                'language': language_name,
                'size': len(content),
                'timestamp': datetime.now().isoformat(),
                'chunking_error': str(e)
            }
        }]


def get_git_repo_info_structured(repo_path: str, chunk_size: int = 4000, chunk_overlap: int = 400) -> Optional[Dict[str, Any]]:
    """
    Extract structured information from a Git repository.
    
    Args:
        repo_path (str): Path to the Git repository
        chunk_size (int): Maximum chunk size in characters
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        Optional[Dict[str, Any]]: Structured repository information
    """
    repo = None
    try:
        repo = git.Repo(repo_path)
        repo_name = os.path.basename(repo_path)
        # Use actual repo name as repo_id (like TalentTalk---AI-powered-interview-system)
        repo_id = repo_name
        
        repo_info = {
            'repo_id': repo_id,
            'repo_name': repo_name,
            'commit_count': len(list(repo.iter_commits())),
            'branches': [branch.name for branch in repo.branches],
            'files': [],  # Keep as 'files' to match old structure
            'chunking_info': {
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'total_chunks': 0,
                'files_chunked': 0,
                'files_not_chunked': 0
            }
        }
        
        # Define file extensions and names to include
        relevant_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.sass', '.less',
            '.md', '.txt', '.rst', '.json', '.yaml', '.yml', '.toml',
            '.sql', '.sh', '.bat', '.ps1', '.proto', '.tex', '.lua', '.pl',
            '.hs', '.ex', '.exs', '.vb', '.sol', '.cob', '.cbl',
            '.dockerfile', '.gitignore', '.env.example'
        }
        
        relevant_filenames = {
            'README', 'LICENSE', 'CHANGELOG', 'CONTRIBUTING', 'INSTALL',
            'Dockerfile', 'Makefile', 'requirements.txt', 'package.json',
            'setup.py', 'pyproject.toml', 'Cargo.toml', 'pom.xml',
            'build.gradle', 'composer.json', 'Gemfile'
        }
        
        skip_directories = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.env', 'build', 'dist', 'target',
            '.idea', '.vscode', 'logs', 'tmp', 'temp',
            'images', 'assets', 'static/images', 'public/images'
        }
        
        # Process files
        tree = repo.head.commit.tree
        for item in tree.traverse():
            if item.type == 'blob':
                # Skip unwanted directories
                if any(skip_dir in item.path for skip_dir in skip_directories):
                    continue
                
                # Check if file should be included
                file_ext = os.path.splitext(item.path)[1].lower()
                filename = os.path.basename(item.path)
                filename_no_ext = os.path.splitext(filename)[0].upper()
                
                should_include = (
                    file_ext in relevant_extensions or
                    filename_no_ext in relevant_filenames or
                    filename in relevant_filenames
                )
                
                if not should_include:
                    continue
                
                try:
                    # Decode file content
                    content = item.data_stream.read().decode('utf-8')
                    if '\x00' in content or len(content) > 500000:  # Skip binary or very large files
                        continue
                    
                    # Process file into structured chunks
                    file_chunks = process_file_structured(
                        item.path, content, repo_name, chunk_size, chunk_overlap
                    )
                    
                    # Add chunks to repo info
                    repo_info['files'].extend(file_chunks)
                    
                    # Update chunking statistics
                    repo_info['chunking_info']['total_chunks'] += len(file_chunks)
                    
                    if len(file_chunks) > 1:
                        repo_info['chunking_info']['files_chunked'] += 1
                    else:
                        repo_info['chunking_info']['files_not_chunked'] += 1
                
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing file {item.path}: {e}")
                    continue
        
        print(f"Processed {len(repo_info['files'])} chunks from {repo_info['repo_name']}")
        print(f"Chunking stats: {repo_info['chunking_info']['files_chunked']} files chunked, "
              f"{repo_info['chunking_info']['files_not_chunked']} files kept whole")
        
        return repo_info
    
    except Exception as e:
        print(f"Error accessing Git repo: {e}")
        return None
    finally:
        if repo is not None:
            repo.close()


def get_repo_name_from_url(url: str) -> str:
    """Extract repository name from URL."""
    path = urlparse(url).path
    return path.strip("/").split("/")[-1]


def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def get_github_repo_info_structured(github_url: str, branch: Optional[str] = None, 
                                   chunk_size: int = 4000, chunk_overlap: int = 400) -> Optional[Dict[str, Any]]:
    """
    Clone a GitHub repo and extract structured information.
    
    Args:
        github_url (str): GitHub repository URL
        branch (Optional[str]): Specific branch to clone
        chunk_size (int): Maximum chunk size
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        Optional[Dict[str, Any]]: Structured repository information
    """
    repo_name = get_repo_name_from_url(github_url)
    base_tmp = tempfile.mkdtemp()
    repo_dir = os.path.join(base_tmp, repo_name)
    repo = None
    
    try:
        repo = Repo.clone_from(github_url, repo_dir, branch=branch)
        result = get_git_repo_info_structured(repo_dir, chunk_size, chunk_overlap)
        
        # Add GitHub-specific metadata
        if result:
            result['source_type'] = 'github'
            result['source_url'] = github_url
            result['branch'] = branch
        
        return result
    except Exception as e:
        print(f"Error cloning GitHub repo: {e}")
        return None
    finally:
        if repo is not None:
            repo.close()
        
        try:
            shutil.rmtree(base_tmp, onerror=remove_readonly)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temp directory: {cleanup_error}")


def get_azure_repo_info_structured(organization: str, project: str, repository: str, 
                                  pat: str, branch: Optional[str] = None,
                                  chunk_size: int = 4000, chunk_overlap: int = 400) -> Optional[Dict[str, Any]]:
    """
    Clone an Azure DevOps repo and extract structured information.
    
    Args:
        organization (str): Azure DevOps organization
        project (str): Project name
        repository (str): Repository name
        pat (str): Personal Access Token
        branch (Optional[str]): Specific branch to clone
        chunk_size (int): Maximum chunk size
        chunk_overlap (int): Overlap between chunks
        
    Returns:
        Optional[Dict[str, Any]]: Structured repository information
    """
    clone_url = f"https://{organization}:{pat}@dev.azure.com/{organization}/{project}/_git/{repository}"
    
    base_tmp = tempfile.mkdtemp()
    repo_dir = os.path.join(base_tmp, repository)
    repo = None
    
    try:
        repo = Repo.clone_from(clone_url, repo_dir, branch=branch)
        result = get_git_repo_info_structured(repo_dir, chunk_size, chunk_overlap)
        
        # Add Azure-specific metadata
        if result:
            result['source_type'] = 'azure_devops'
            result['organization'] = organization
            result['project'] = project
            result['azure_repo_name'] = repository
            result['branch'] = branch
        
        return result
    except Exception as e:
        print(f"Error cloning Azure DevOps repo: {e}")
        return None
    finally:
        if repo is not None:
            repo.close()
        
        try:
            shutil.rmtree(base_tmp, onerror=remove_readonly)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temp directory: {cleanup_error}")


# Aliases for backward compatibility
get_github_repo_info = get_github_repo_info_structured
get_azure_repo_info = get_azure_repo_info_structured


# Example usage and testing
if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("🔍 Testing Structured Git Utils")
    print("=" * 50)
    
    # Test with GitHub repository
    github_url = "https://github.com/M-Mowina/LinkedIn-Booster"
    
    print(f"Processing: {github_url}")
    repo_data = get_github_repo_info_structured(github_url, chunk_size=3000, chunk_overlap=300)
    
    if repo_data:
        print(f"\n✅ Repository: {repo_data['repo_name']}")
        print(f"📊 Statistics:")
        stats = repo_data['statistics']
        print(f"   Files: {stats['total_files']}")
        print(f"   Chunks: {stats['total_chunks']}")
        print(f"   Chunked files: {stats['chunked_files']}")
        print(f"   Languages: {list(stats['languages'].keys())}")
        print(f"   Total symbols: {sum(stats['symbol_counts'].values())}")
        print(f"   Total imports: {stats['total_imports']}")
        
        # Show example chunks
        print(f"\n🔍 Example chunks:")
        for i, chunk in enumerate(repo_data['chunks'][:3]):
            print(f"\n{i+1}. ID: {chunk['id']}")
            print(f"   File: {chunk['file_path']}")
            print(f"   Language: {chunk['metadata']['language']}")
            print(f"   Chunk: {chunk['chunk_id'] + 1}/{chunk['total_chunks']}")
            print(f"   Size: {chunk['metadata']['chunk_size']} chars")
            print(f"   Symbols: {sum(len(v) for v in chunk['symbols'].values())}")
            print(f"   Imports: {len(chunk['imports'])}")
            
            if chunk['symbols']:
                print(f"   Symbol types: {list(chunk['symbols'].keys())}")
            
            if chunk['imports']:
                print(f"   Sample imports: {chunk['imports'][:2]}")
        
        # Save sample to JSON for inspection
        sample_data = {
            'repo_info': {
                'repo_id': repo_data['repo_id'],
                'repo_name': repo_data['repo_name'],
                'statistics': repo_data['statistics']
            },
            'sample_chunks': repo_data['chunks'][:2]  # First 2 chunks
        }
        
        with open('sample_structured_output.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"\n💾 Sample data saved to 'sample_structured_output.json'")
    
    else:
        print("❌ Failed to process repository")
    
    print("\n✅ Testing completed!")