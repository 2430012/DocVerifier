from abc import ABC, abstractmethod
from typing import List
from ..models import CodeElement

class BaseParser(ABC):
    @abstractmethod
    def parse(self, source_code: str) -> List[CodeElement]:
        """Parse source code and extract documentable code elements."""
        pass

    def extract_documentation(self, node) -> str:
    return ""
