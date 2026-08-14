from .base_parser import BaseParser
from .python_parser import PythonParser
from .java_parser import JavaParser
from .cpp_parser import CppParser
from .kotlin_parser import KotlinParser

def get_parser(language: str) -> BaseParser:
    parsers = {
        'python': PythonParser,
        'java': JavaParser,
        'cpp': CppParser,
        'kotlin': KotlinParser
    }
    
    parser_class = parsers.get(language.lower())
    if not parser_class:
        raise ValueError(f"Unsupported language: {language}")
    
    return parser_class()
