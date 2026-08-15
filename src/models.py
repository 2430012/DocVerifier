from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DocParameter:
    name: str
    description: Optional[str] = None
    type: Optional[str] = None

@dataclass
class DocReturn:
    description: Optional[str] = None
    type: Optional[str] = None

@dataclass
class Documentation:
    raw_text: str = ""
    description: str = ""
    parameters: List[DocParameter] = field(default_factory=list)
    returns: Optional[DocReturn] = None
    exceptions: List[str] = field(default_factory=list)

@dataclass
class CodeElement:
    name: str
    type: str # 'function', 'class', 'method'
    start_line: int
    end_line: int
    parameters: List[str] = field(default_factory=list)
    has_return: bool = False
    source_code: str = ""
    documentation: Optional[Documentation] = None

@dataclass
class MetricResult:
    coverage: float # 0 to 1
    completeness: float # 0 to 1
    coherence: float # 0 to 1
    readability: float # 0 to 1
    semantic_similarity: Optional[float] = None
    issues: List[str] = field(default_factory=list)

@dataclass
class VerificationResult:
    element: CodeElement
    metrics: MetricResult
