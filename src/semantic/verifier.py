try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from typing import List
from ..models import VerificationResult

class SemanticVerifier:
    def __init__(self, model_name="microsoft/codebert-base"):
        if not HAS_TORCH:
            print("Warning: Torch/Transformers not installed. Semantic verification disabled.")
            self.active = False
            return
            
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.active = True
        except Exception as e:
            print(f"Warning: Could not load Semantic Model ({e}). Semantic verification will be disabled.")
            self.active = False

    def verify(self, results: List[VerificationResult]) -> None:
        if not self.active:
            return
            
        for res in results:
            if res.metrics.coverage == 0.0 or not res.element.documentation:
                continue
                
            code_snippet = res.element.source_code
            doc_text = res.element.documentation.description
            
            similarity = self._compute_similarity(code_snippet, doc_text)
            res.metrics.semantic_similarity = similarity
            
            if similarity < 0.5:
                res.metrics.issues.append(f"Low semantic similarity between code and documentation ({similarity:.2f}).")

    def _compute_similarity(self, code: str, doc: str) -> float:
        # Tokenize
        code_tokens = self.tokenizer(code, return_tensors="pt", truncation=True, max_length=256).to(self.device)
        doc_tokens = self.tokenizer(doc, return_tensors="pt", truncation=True, max_length=256).to(self.device)
        
        with torch.no_grad():
            code_emb = self.model(**code_tokens).pooler_output
            doc_emb = self.model(**doc_tokens).pooler_output
            
        similarity = F.cosine_similarity(code_emb, doc_emb).item()
        return float(max(0.0, similarity))
