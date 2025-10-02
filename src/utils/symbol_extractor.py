"""
Multi-language symbol extractor using tree-sitter.
Extracts imports, functions, classes, and other symbols from various programming languages.
"""

import os
from typing import Dict, List, Optional, Any
from langchain_text_splitters import Language

# Tree-sitter language imports
try:
    import tree_sitter_python as tspython
    from tree_sitter import Language as TSLanguage, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️  tree-sitter not available. Install with: pip install tree-sitter tree-sitter-python")

# Additional language imports (install as needed)
LANGUAGE_MODULES = {
    'python': 'tree_sitter_python',
    'javascript': 'tree_sitter_javascript', 
    'typescript': 'tree_sitter_typescript',
    'java': 'tree_sitter_java',
    'cpp': 'tree_sitter_cpp',
    'c': 'tree_sitter_c',
    'go': 'tree_sitter_go',
    'rust': 'tree_sitter_rust',
    'ruby': 'tree_sitter_ruby',
    'php': 'tree_sitter_php',
    'csharp': 'tree_sitter_c_sharp',
    'swift': 'tree_sitter_swift',
    'kotlin': 'tree_sitter_kotlin',
}


class SymbolExtractor:
    """Multi-language symbol extractor using tree-sitter."""
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        self._initialize_languages()
    
    def _initialize_languages(self):
        """Initialize available tree-sitter languages."""
        if not TREE_SITTER_AVAILABLE:
            return
        
        # Initialize Python (most commonly available)
        try:
            self.languages['python'] = TSLanguage(tspython.language())
            self.parsers['python'] = Parser(self.languages['python'])
        except Exception as e:
            print(f"⚠️  Failed to initialize Python parser: {e}")
        
        # Try to initialize other languages
        for lang_name, module_name in LANGUAGE_MODULES.items():
            if lang_name == 'python':  # Already handled
                continue
            
            try:
                module = __import__(module_name)
                self.languages[lang_name] = TSLanguage(module.language())
                self.parsers[lang_name] = Parser(self.languages[lang_name])
            except ImportError:
                # Language module not installed
                continue
            except Exception as e:
                print(f"⚠️  Failed to initialize {lang_name} parser: {e}")
    
    def get_language_from_extension(self, file_path: str) -> Optional[str]:
        """Map file extension to language name."""
        ext = os.path.splitext(file_path)[1].lower()
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
        }
        
        return extension_map.get(ext)
    
    def extract_symbols(self, code: str, language: str) -> Dict[str, List[str]]:
        """
        Extract symbols from code using tree-sitter.
        
        Args:
            code (str): Source code
            language (str): Programming language
            
        Returns:
            Dict[str, List[str]]: Dictionary with symbol types and their names
        """
        if not TREE_SITTER_AVAILABLE or language not in self.parsers:
            return self._fallback_extraction(code, language)
        
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))
            
            # Use language-specific extraction
            if language == 'python':
                return self._extract_python_symbols(tree.root_node)
            elif language in ['javascript', 'typescript']:
                return self._extract_js_ts_symbols(tree.root_node)
            elif language == 'java':
                return self._extract_java_symbols(tree.root_node)
            elif language in ['cpp', 'c']:
                return self._extract_c_cpp_symbols(tree.root_node)
            elif language == 'go':
                return self._extract_go_symbols(tree.root_node)
            elif language == 'rust':
                return self._extract_rust_symbols(tree.root_node)
            elif language == 'ruby':
                return self._extract_ruby_symbols(tree.root_node)
            elif language == 'php':
                return self._extract_php_symbols(tree.root_node)
            elif language == 'csharp':
                return self._extract_csharp_symbols(tree.root_node)
            elif language == 'swift':
                return self._extract_swift_symbols(tree.root_node)
            elif language == 'kotlin':
                return self._extract_kotlin_symbols(tree.root_node)
            else:
                return self._extract_generic_symbols(tree.root_node)
                
        except Exception as e:
            print(f"⚠️  Tree-sitter extraction failed for {language}: {e}")
            return self._fallback_extraction(code, language)
    
    def _extract_python_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Python symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'variables': [],
            'decorators': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_statement':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'import_from_statement':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'decorator':
                symbols['decorators'].append(node.text.decode('utf8').strip())
            elif node.type == 'assignment':
                # Extract variable assignments at module level
                if node.parent and node.parent.type == 'module':
                    left = node.child_by_field_name('left')
                    if left and left.type == 'identifier':
                        symbols['variables'].append(left.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_js_ts_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract JavaScript/TypeScript symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'variables': [],
            'exports': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_statement':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'variable_declaration':
                for child in node.children:
                    if child.type == 'variable_declarator':
                        name_node = child.child_by_field_name('name')
                        if name_node:
                            symbols['variables'].append(name_node.text.decode('utf8'))
            elif node.type == 'export_statement':
                symbols['exports'].append(node.text.decode('utf8').strip())
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_java_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Java symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'interfaces': [],
            'packages': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_declaration':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'package_declaration':
                symbols['packages'].append(node.text.decode('utf8').strip())
            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['interfaces'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_c_cpp_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract C/C++ symbols."""
        symbols = {
            'includes': [],
            'functions': [],
            'classes': [],
            'structs': [],
            'defines': []
        }
        
        def traverse(node: Node):
            if node.type == 'preproc_include':
                symbols['includes'].append(node.text.decode('utf8').strip())
            elif node.type == 'preproc_def':
                symbols['defines'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_definition':
                declarator = node.child_by_field_name('declarator')
                if declarator:
                    name_node = self._find_function_name(declarator)
                    if name_node:
                        symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_specifier':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'struct_specifier':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['structs'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_go_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Go symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'types': [],
            'variables': [],
            'constants': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_spec':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'type_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['types'].append(name_node.text.decode('utf8'))
            elif node.type == 'var_declaration':
                symbols['variables'].append(node.text.decode('utf8').strip())
            elif node.type == 'const_declaration':
                symbols['constants'].append(node.text.decode('utf8').strip())
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_rust_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Rust symbols."""
        symbols = {
            'uses': [],
            'functions': [],
            'structs': [],
            'enums': [],
            'traits': [],
            'impls': []
        }
        
        def traverse(node: Node):
            if node.type == 'use_declaration':
                symbols['uses'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'struct_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['structs'].append(name_node.text.decode('utf8'))
            elif node.type == 'enum_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['enums'].append(name_node.text.decode('utf8'))
            elif node.type == 'trait_item':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['traits'].append(name_node.text.decode('utf8'))
            elif node.type == 'impl_item':
                symbols['impls'].append('impl block')
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_ruby_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Ruby symbols."""
        symbols = {
            'requires': [],
            'functions': [],
            'classes': [],
            'modules': [],
            'constants': []
        }
        
        def traverse(node: Node):
            if node.type == 'call' and node.children:
                method_node = node.children[0]
                if method_node.text.decode('utf8') == 'require':
                    symbols['requires'].append(node.text.decode('utf8').strip())
            elif node.type == 'method':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'module':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['modules'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_php_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract PHP symbols."""
        symbols = {
            'includes': [],
            'functions': [],
            'classes': [],
            'interfaces': [],
            'traits': [],
            'namespaces': []
        }
        
        def traverse(node: Node):
            if node.type == 'include_expression' or node.type == 'require_expression':
                symbols['includes'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['interfaces'].append(name_node.text.decode('utf8'))
            elif node.type == 'trait_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['traits'].append(name_node.text.decode('utf8'))
            elif node.type == 'namespace_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['namespaces'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_csharp_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract C# symbols."""
        symbols = {
            'usings': [],
            'functions': [],
            'classes': [],
            'interfaces': [],
            'namespaces': []
        }
        
        def traverse(node: Node):
            if node.type == 'using_directive':
                symbols['usings'].append(node.text.decode('utf8').strip())
            elif node.type == 'method_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['interfaces'].append(name_node.text.decode('utf8'))
            elif node.type == 'namespace_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['namespaces'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_swift_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Swift symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'structs': [],
            'protocols': [],
            'extensions': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_declaration':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'struct_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['structs'].append(name_node.text.decode('utf8'))
            elif node.type == 'protocol_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['protocols'].append(name_node.text.decode('utf8'))
            elif node.type == 'extension_declaration':
                symbols['extensions'].append('extension')
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_kotlin_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Extract Kotlin symbols."""
        symbols = {
            'imports': [],
            'functions': [],
            'classes': [],
            'interfaces': [],
            'objects': [],
            'packages': []
        }
        
        def traverse(node: Node):
            if node.type == 'import_header':
                symbols['imports'].append(node.text.decode('utf8').strip())
            elif node.type == 'package_header':
                symbols['packages'].append(node.text.decode('utf8').strip())
            elif node.type == 'function_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['functions'].append(name_node.text.decode('utf8'))
            elif node.type == 'class_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['classes'].append(name_node.text.decode('utf8'))
            elif node.type == 'interface_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['interfaces'].append(name_node.text.decode('utf8'))
            elif node.type == 'object_declaration':
                name_node = node.child_by_field_name('name')
                if name_node:
                    symbols['objects'].append(name_node.text.decode('utf8'))
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _extract_generic_symbols(self, root_node: Node) -> Dict[str, List[str]]:
        """Generic symbol extraction for unsupported languages."""
        symbols = {
            'identifiers': [],
            'strings': [],
            'comments': []
        }
        
        def traverse(node: Node):
            if node.type == 'identifier':
                symbols['identifiers'].append(node.text.decode('utf8'))
            elif node.type == 'string':
                symbols['strings'].append(node.text.decode('utf8'))
            elif 'comment' in node.type:
                symbols['comments'].append(node.text.decode('utf8').strip())
            
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return symbols
    
    def _fallback_extraction(self, code: str, language: str) -> Dict[str, List[str]]:
        """Fallback regex-based extraction when tree-sitter is not available."""
        import re
        
        patterns = {
            'python': {
                'imports': [
                    r'^import\s+[\w\.]+(?:\s+as\s+\w+)?',
                    r'^from\s+[\w\.]+\s+import\s+.+'
                ],
                'functions': [r'^def\s+(\w+)\s*\('],
                'classes': [r'^class\s+(\w+)(?:\s*\(.*?\))?:']
            },
            'javascript': {
                'imports': [
                    r'import\s+.*?from\s+[\'"][^\'"]+[\'"]',
                    r'const\s+.*?=\s+require\([\'"][^\'"]+[\'"]\)'
                ],
                'functions': [
                    r'function\s+(\w+)\s*\(',
                    r'(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>)'
                ],
                'classes': [r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{']
            }
        }
        
        symbols = {'imports': [], 'functions': [], 'classes': []}
        
        if language in patterns:
            for symbol_type, pattern_list in patterns[language].items():
                for pattern in pattern_list:
                    matches = re.findall(pattern, code, re.MULTILINE)
                    symbols[symbol_type].extend(matches)
        
        return symbols
    
    def _find_function_name(self, node: Node) -> Optional[Node]:
        """Helper to find function name in C/C++ declarators."""
        if node.type == 'identifier':
            return node
        
        for child in node.children:
            result = self._find_function_name(child)
            if result:
                return result
        
        return None
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages."""
        return list(self.parsers.keys())
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        return language in self.parsers


# Global instance
symbol_extractor = SymbolExtractor()


def extract_file_symbols(file_path: str, content: str) -> Dict[str, List[str]]:
    """
    Convenience function to extract symbols from a file.
    
    Args:
        file_path (str): Path to the file (used for language detection)
        content (str): File content
        
    Returns:
        Dict[str, List[str]]: Extracted symbols
    """
    language = symbol_extractor.get_language_from_extension(file_path)
    
    if not language:
        return {'error': ['Unsupported file type']}
    
    return symbol_extractor.extract_symbols(content, language)


def create_symbol_summary(symbols: Dict[str, List[str]], max_items: int = 10) -> str:
    """
    Create a human-readable summary of extracted symbols.
    
    Args:
        symbols (Dict[str, List[str]]): Extracted symbols
        max_items (int): Maximum items per category
        
    Returns:
        str: Formatted summary
    """
    summary_parts = []
    
    for symbol_type, items in symbols.items():
        if items and symbol_type != 'error':
            display_items = items[:max_items]
            if len(items) > max_items:
                display_items.append(f"... and {len(items) - max_items} more")
            
            summary_parts.append(f"{symbol_type.upper()}: {', '.join(display_items)}")
    
    return " | ".join(summary_parts) if summary_parts else "No symbols found"


if __name__ == "__main__":
    # Test the symbol extractor
    print("🔍 Testing Multi-Language Symbol Extractor")
    print("=" * 50)
    
    # Test Python code
    python_code = '''
import os
from typing import Dict, List
import numpy as np

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process_data(self, input_data):
        return input_data.upper()

def main():
    processor = DataProcessor()
    return processor.process_data("hello")

if __name__ == "__main__":
    main()
'''
    
    print("🐍 Python symbols:")
    python_symbols = symbol_extractor.extract_symbols(python_code, 'python')
    print(f"Python Symbols: {python_symbols}")
    print(create_symbol_summary(python_symbols))
    
    # Test JavaScript code
    js_code = '''
import React from 'react';
import { useState, useEffect } from 'react';

class Component extends React.Component {
    constructor(props) {
        super(props);
    }
    
    render() {
        return <div>Hello</div>;
    }
}

function useCustomHook() {
    const [state, setState] = useState(null);
    return state;
}

export default Component;
'''
    
    print("\n🟨 JavaScript symbols:")
    js_symbols = symbol_extractor.extract_symbols(js_code, 'javascript')
    print(f"JavaScript Symbols{'js_symbols'}")
    print(create_symbol_summary(js_symbols))
    
    print(f"\n✅ Available languages: {symbol_extractor.get_available_languages()}")