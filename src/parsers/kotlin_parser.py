import tree_sitter_kotlin as tskotlin
from tree_sitter import Language, Parser
from typing import List
import re
from .base_parser import BaseParser
from ..models import CodeElement, Documentation, DocParameter, DocReturn

class KotlinParser(BaseParser):
    def __init__(self):
        self.language = Language(tskotlin.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: str) -> List[CodeElement]:
        source_bytes = source_code.encode("utf8")
        tree = self.parser.parse(source_bytes)
        return self._traverse(tree.root_node, source_bytes)

    def _traverse(self, node, source_bytes: bytes, last_comment: str = None) -> List[CodeElement]:
        elements = []
        current_comment = last_comment

        for child in node.children:
            # KDoc comments are 'multiline_comment' in tree-sitter-kotlin
            if child.type in ('multiline_comment', 'comment'):
                comment_text = child.text.decode("utf8")
                if comment_text.startswith('/**'):
                    current_comment = comment_text

            elif child.type in ['function_declaration', 'class_declaration']:
                # For class_declaration, the name is the 'simple_identifier' field.
                # For data classes: modifiers -> 'data' + class_declaration whose first
                # simple_identifier child is the name.
                name_node = child.child_by_field_name('simple_identifier')

                # Fallback: walk children for the first simple_identifier
                if not name_node:
                    for c in child.children:
                        if c.type == 'simple_identifier':
                            name_node = c
                            break

                name = name_node.text.decode("utf8") if name_node else "unknown"

                elem = CodeElement(
                    name=name,
                    type='function' if child.type == 'function_declaration' else 'class',
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    source_code=child.text.decode("utf8")
                )

                if child.type == 'function_declaration':
                    # Extract params from AST via 'function_value_parameters' node
                    for c in child.children:
                        if c.type == 'function_value_parameters':
                            for param in c.children:
                                if param.type == 'function_value_parameter':
                                    p_node = param.child_by_field_name('simple_identifier')
                                    if not p_node:
                                        for gc in param.children:
                                            if gc.type == 'simple_identifier':
                                                p_node = gc
                                                break
                                    if p_node:
                                        elem.parameters.append(p_node.text.decode("utf8"))
                            break

                    # Detect return type via 'type_reference' after ':'
                    func_text = child.text.decode("utf8")
                    ret_match = re.search(r'\)\s*:\s*([^\s{=]+)', func_text)
                    if ret_match:
                        elem.has_return = ret_match.group(1).strip() not in ('Unit', 'Unit?', 'Nothing')

                if current_comment:
                    elem.documentation = Documentation(raw_text=current_comment, description="")
                    self.extract_documentation(elem)

                elements.append(elem)
                current_comment = None

                elements.extend(self._traverse(child, source_bytes, current_comment))

            else:
                elements.extend(self._traverse(child, source_bytes, current_comment))
                if child.type not in ('modifiers', 'annotation', 'class_modifier',
                                      'function_modifier', 'member_modifier'):
                    current_comment = None

        return elements

def extract_documentation(self, element: CodeElement) -> None:
        if not element.documentation:
            return

        text = element.documentation.raw_text

        # ARREGLO: Agregar MULTILINE y manejar indentación en KDoc
        text = re.sub(r'^[ \t]*/\*\*|\*/[ \t]*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[ \t]*\*[ \t]?', '', text, flags=re.MULTILINE)

        doc = element.documentation

        # Extraer descripción
        desc_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('@'):
                break
            if stripped:
                desc_lines.append(stripped)
        doc.description = ' '.join(desc_lines)

        # Extraer parámetros
        for match in re.finditer(r'@param\s+(\w+)\s+(.*)', text):
            doc.parameters.append(DocParameter(name=match.group(1), description=match.group(2).strip()))

        # Extraer retorno
        ret_match = re.search(r'@returns?\s+(.*)', text)
        if ret_match:
            doc.returns = DocReturn(description=ret_match.group(1).strip())
