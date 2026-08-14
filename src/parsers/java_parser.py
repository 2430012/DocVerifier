import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
from typing import List
import re
from .base_parser import BaseParser
from ..models import CodeElement, Documentation, DocParameter, DocReturn

class JavaParser(BaseParser):
    def __init__(self):
        self.language = Language(tsjava.language())
        self.parser = Parser(self.language)

    def parse(self, source_code: str) -> List[CodeElement]:
        source_bytes = source_code.encode("utf8")
        tree = self.parser.parse(source_bytes)
        return self._traverse(tree.root_node, source_bytes)

    def _traverse(self, node, source_bytes: bytes, last_comment: str = None) -> List[CodeElement]:
        elements = []
        current_comment = last_comment

        for child in node.children:
            if child.type == 'block_comment':
                comment_text = child.text.decode("utf8")
                if comment_text.startswith('/**'):
                    current_comment = comment_text

            elif child.type in ['method_declaration', 'class_declaration']:
                name_node = child.child_by_field_name('name')
                # Use node.text for safe name extraction (no byte-offset bugs)
                name = name_node.text.decode("utf8") if name_node else "unknown"

                elem = CodeElement(
                    name=name,
                    type='method' if child.type == 'method_declaration' else 'class',
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                    source_code=child.text.decode("utf8")
                )

                if child.type == 'method_declaration':
                    params_node = child.child_by_field_name('parameters')
                    if params_node:
                        for param in params_node.children:
                            if param.type == 'formal_parameter':
                                p_name_node = param.child_by_field_name('name')
                                if p_name_node:
                                    elem.parameters.append(p_name_node.text.decode("utf8"))

                    return_type_node = child.child_by_field_name('type')
                    if return_type_node:
                        ret_type_str = return_type_node.text.decode("utf8")
                        elem.has_return = ret_type_str != 'void'

                if current_comment:
                    elem.documentation = Documentation(raw_text=current_comment, description="")
                    self.extract_documentation(elem)

                elements.append(elem)
                current_comment = None

                elements.extend(self._traverse(child, source_bytes, current_comment))

            else:
                elements.extend(self._traverse(child, source_bytes, current_comment))
                if child.type not in ['modifiers', 'annotation']:
                    current_comment = None

        return elements

    def extract_documentation(self, element: CodeElement) -> None:
        if not element.documentation:
            return

        text = element.documentation.raw_text

        # Clean Javadoc markers using real newlines
        text = re.sub(r'^/\*\*|\*/$', '', text)
        text = re.sub(r'^[ \t]*\*[ \t]?', '', text, flags=re.MULTILINE)

        doc = element.documentation

        # Extract description (lines before first @tag)
        desc_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith('@'):
                break
            if stripped:
                desc_lines.append(stripped)
        doc.description = ' '.join(desc_lines)

        # @param tag
        for match in re.finditer(r'@param\s+(\w+)\s+(.*)', text):
            doc.parameters.append(DocParameter(name=match.group(1), description=match.group(2).strip()))

        # @return tag
        ret_match = re.search(r'@returns?\s+(.*)', text)
        if ret_match:
            doc.returns = DocReturn(description=ret_match.group(1).strip())

        # @throws / @exception
        for match in re.finditer(r'@throws\s+(\w+)\s+(.*)|@exception\s+(\w+)\s+(.*)', text):
            doc.exceptions.append(match.group(1) or match.group(3))
