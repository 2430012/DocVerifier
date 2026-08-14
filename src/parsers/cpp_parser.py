import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser
from typing import List
import re
from .base_parser import BaseParser
from ..models import CodeElement, Documentation, DocParameter, DocReturn

class CppParser(BaseParser):
    def __init__(self):
        self.language = Language(tscpp.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: str) -> List[CodeElement]:
        source_bytes = source_code.encode("utf8")
        tree = self.parser.parse(source_bytes)
        return self._traverse(tree.root_node, source_bytes)

    def _traverse(self, node, source_bytes: bytes, last_comment: str = None) -> List[CodeElement]:
        elements = []
        current_comment = last_comment

        for child in node.children:
            if child.type == 'comment':
                comment_text = child.text.decode("utf8")
                if comment_text.startswith('/**') or comment_text.startswith('/*!') or comment_text.startswith('///'):
                    current_comment = comment_text

            elif child.type in ['function_definition', 'class_specifier']:
                name = "unknown"

                if child.type == 'function_definition':
                    decl_node = child.child_by_field_name('declarator')
                    if decl_node:
                        # Handle qualified names, pointers, references, etc.
                        if decl_node.type == 'function_declarator':
                            inner = decl_node.child_by_field_name('declarator')
                            if inner:
                                name = inner.text.decode("utf8")
                        else:
                            name = decl_node.text.decode("utf8")
                else:
                    name_node = child.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode("utf8")

                elem = CodeElement(
                    name=name,
                    type='function' if child.type == 'function_definition' else 'class',
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    source_code=child.text.decode("utf8")
                )

                # Extract parameters for functions
                if child.type == 'function_definition':
                    decl_node = child.child_by_field_name('declarator')
                    if decl_node and decl_node.type == 'function_declarator':
                        params_node = decl_node.child_by_field_name('parameters')
                        if params_node:
                            for param in params_node.children:
                                if param.type == 'parameter_declaration':
                                    decl = param.child_by_field_name('declarator')
                                    if decl:
                                        elem.parameters.append(decl.text.decode("utf8"))

                    return_type_node = child.child_by_field_name('type')
                    if return_type_node:
                        ret_type_str = return_type_node.text.decode("utf8")
                        elem.has_return = ret_type_str not in ('void', 'void ')

                if current_comment:
                    elem.documentation = Documentation(raw_text=current_comment, description="")
                    self.extract_documentation(elem)

                elements.append(elem)
                current_comment = None

                elements.extend(self._traverse(child, source_bytes, current_comment))

            else:
                elements.extend(self._traverse(child, source_bytes, current_comment))
                if child.type not in ['modifiers', 'template_declaration', 'access_specifier']:
                    current_comment = None

        return elements

def extract_documentation(self, element: CodeElement) -> None:
        if not element.documentation:
            return

        text = element.documentation.raw_text

        text = re.sub(r'^[ \t]*/\*\*|^[ \t]*/\*!|\*/[ \t]*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*///[ \t]?|^[ \t]*//![ \t]?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*\*[ \t]?', '', text, flags=re.MULTILINE)

        doc = element.documentation

        # Extraer descripción
        desc_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('@') or stripped.startswith('\\'):
                break
            if stripped:
                desc_lines.append(stripped)
        doc.description = ' '.join(desc_lines)

        # Extraer parámetros (@param o \param)
        for match in re.finditer(r'[@\\]param\s+(\w+)\s+(.*)', text):
            doc.parameters.append(DocParameter(name=match.group(1), description=match.group(2).strip()))

        # Extraer retorno (@return o \return)
        ret_match = re.search(r'[@\\]returns?\s+(.*)', text)
        if ret_match:
            doc.returns = DocReturn(description=ret_match.group(1).strip())
