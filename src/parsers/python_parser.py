import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from typing import List
import re
from .base_parser import BaseParser
from ..models import CodeElement, Documentation, DocParameter, DocReturn

class PythonParser(BaseParser):
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: str) -> List[CodeElement]:
        source_bytes = source_code.encode("utf8")
        tree = self.parser.parse(source_bytes)
        return self._traverse(tree.root_node, source_bytes)

    # Python implicit params that should never require documentation
    IMPLICIT_PARAMS = {'self', 'cls'}

    def _traverse(self, node, source_bytes: bytes) -> List[CodeElement]:
        elements = []
        if node.type in ['function_definition', 'class_definition']:
            name_node = node.child_by_field_name('name')
            # Use node.text for safe, byte-accurate name extraction
            name = name_node.text.decode('utf8') if name_node else 'unknown'

            elem = CodeElement(
                name=name,
                type='function' if node.type == 'function_definition' else 'class',
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
                source_code=node.text.decode('utf8')
            )

            # Extract parameters for functions (excluding self/cls)
            if node.type == 'function_definition':
                params_node = node.child_by_field_name('parameters')
                if params_node:
                    for child in params_node.children:
                        param_name = None
                        if child.type == 'identifier':
                            param_name = child.text.decode('utf8')
                        elif child.type in ('typed_parameter', 'default_parameter', 'typed_default_parameter'):
                            ident = child.child(0)
                            if ident and ident.type == 'identifier':
                                param_name = ident.text.decode('utf8')
                        if param_name and param_name not in self.IMPLICIT_PARAMS:
                            elem.parameters.append(param_name)

                return_type_node = node.child_by_field_name('return_type')
                elem.has_return = return_type_node is not None

            # Extract docstring (first statement of body if it is a string literal)
            body_node = node.child_by_field_name('body')
            if body_node and len(body_node.children) > 0:
                first_stmt = body_node.children[0]
                if first_stmt.type == 'expression_statement':
                    string_node = first_stmt.children[0]
                    if string_node.type == 'string':
                        doc_str = string_node.text.decode('utf8')
                        # Strip surrounding quotes
                        for q in ('"""', "'''", '"', "'"):
                            if doc_str.startswith(q):
                                doc_str = doc_str[len(q):-len(q)]
                                break
                        elem.documentation = Documentation(raw_text=doc_str, description='')
                        self.extract_documentation(elem)

            elements.append(elem)

        for child in node.children:
            elements.extend(self._traverse(child, source_bytes))

        return elements

    def extract_documentation(self, element: CodeElement) -> None:
        """Parse the raw docstring into structured Documentation fields."""
        if not element.documentation:
            return

        doc = element.documentation
        text = doc.raw_text

        # Use real newlines (the raw string already contains them from tree-sitter)
        # Extract the first paragraph as the description (before any tag line)
        desc_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(':') or stripped.startswith('@'):
                break
            desc_lines.append(stripped)
        doc.description = ' '.join(l for l in desc_lines if l)

        # Sphinx / reStructuredText :param name: desc
        for match in re.finditer(r':param\s+(?:\w+\s+)?(\w+)\s*:(.*)', text):
            name = match.group(1)
            if name not in self.IMPLICIT_PARAMS:
                doc.parameters.append(DocParameter(name=name, description=match.group(2).strip()))

        # :return: / :returns:
        ret_match = re.search(r':returns?\s*:(.*)', text, re.IGNORECASE)
        if ret_match:
            doc.returns = DocReturn(description=ret_match.group(1).strip())
