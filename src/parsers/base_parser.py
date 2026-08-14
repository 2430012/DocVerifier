from abc import ABC, abstractmethod
from typing import List
from ..models import CodeElement

class BaseParser(ABC):
    @abstractmethod
    def parse(self, source_code: str) -> List[CodeElement]:
        """Parse source code and extract documentable code elements."""
        pass

    def extract_documentation(self, node) -> str:
        if not node:
            return ""

        # Si el nodo ya trae un docstring extraído
        if hasattr(node, 'docstring') and node.docstring:
            return str(node.docstring)

        # Recorrer los nodos previos en Tree-sitter para capturar comentarios
        comments = []
        curr = getattr(node, 'prev_sibling', None)
        while curr:
            node_type = str(getattr(curr, 'type', ''))
            if 'comment' in node_type:
                raw_text = getattr(curr, 'text', b'')
                text = raw_text.decode('utf-8', errors='ignore') if isinstance(raw_text, bytes) else str(raw_text)
                comments.insert(0, text.strip())
                curr = getattr(curr, 'prev_sibling', None)
            elif node_type.strip() in ('', '\n', ' ') or not node_type.strip():
                curr = getattr(curr, 'prev_sibling', None)
            else:
                break
                
        if comments:
            return "\n".join(comments)

        return ""
