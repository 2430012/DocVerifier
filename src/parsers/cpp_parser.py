import re
from typing import List, Optional
import tree_sitter_cpp as tspython
from tree_sitter import Language, Parser
from .base_parser import BaseParser
from ..models import CodeElement, Documentation, DocParameter, DocReturn

CPP_LANGUAGE = Language(tspython.language())

class CppParser(BaseParser):
    def __init__(self):
        self.parser = Parser(CPP_LANGUAGE)

    def parse(self, source_code: str) -> List[CodeElement]:
        tree = self.parser.parse(bytes(source_code, "utf-8"))
        elements = []
        self._traverse(tree.root_node, bytes(source_code, "utf-8"), None, elements)
        return elements

    def _parse_doxygen(self, raw_text: str) -> Documentation:
        doc = Documentation(raw_text=raw_text)
        if not raw_text:
            return doc

        text = re.sub(r'^\s*/\*[*!]?|\s*\*/$', '', raw_text, flags=re.MULTILINE)
        text = re.sub(r'^\s*///?|^\s*\* ?', '', text, flags=re.MULTILINE)

        desc_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('@') or stripped.startswith('\\'):
                break
            if stripped:
                desc_lines.append(stripped)
        doc.description = ' '.join(desc_lines)

        for match in re.finditer(r'[@\\]param(?:\[in\]|\[out\]|\[in,out\])?\s+(\w+)\s+(.*)', text):
            doc.parameters.append(DocParameter(name=match.group(1), description=match.group(2).strip()))

        ret_match = re.search(r'[@\\]returns?\s+(.*)', text)
        if not ret_match:
            ret_match = re.search(r'\\returns?\s+(.*)', text)
        if ret_match:
            doc.returns = DocReturn(description=ret_match.group(1).strip())

        return doc

    def _traverse(self, node, source_bytes: bytes, current_comment: Optional[str], elements: List[CodeElement]):
        if node.type == 'comment':
            comment_text = source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            current_comment = (current_comment + "\n" + comment_text) if current_comment else comment_text

        elif node.type in ['class_specifier', 'struct_specifier']:
            name_node = node.child_by_field_name('name')
            name = source_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='ignore') if name_node else 'AnonymousClass'
            doc = self._parse_doxygen(current_comment) if current_comment else None
            elements.append(CodeElement(
                name=name,
                type='Class' if node.type == 'class_specifier' else 'Struct',
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                documentation=doc,
                parameters=[]
            ))
            current_comment = None

        elif node.type in ['function_definition', 'field_declaration', 'function_declarator']:
            code_text = source_bytes[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
            name_match = re.search(r'(\b\w+)\s*\(', code_text)
            
            if name_match:
                name = name_match.group(1)
                params = []
                param_match = re.search(r'\((.*?)\)', code_text, re.DOTALL)
                if param_match:
                    p_str = param_match.group(1).strip()
                    if p_str and p_str != 'void':
                        for p in p_str.split(','):
                            p_parts = p.strip().split()
                            if p_parts:
                                p_name = p_parts[-1].replace('*', '').replace('&', '')
                                if p_name:
                                    params.append(p_name)

                doc = self._parse_doxygen(current_comment) if current_comment else None
                if not any(e.name == name and e.start_line == node.start_point[0] + 1 for e in elements):
                    elements.append(CodeElement(
                        name=name,
                        type='Function',
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        documentation=doc,
                        parameters=params
                    ))
                current_comment = None

        for child in node.children:
            self._traverse(child, source_bytes, current_comment, elements)
            if child.type not in ['modifiers', 'template_declaration', 'access_specifier', 'comment']:
                current_comment = None
