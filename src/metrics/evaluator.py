from typing import List
from ..models import CodeElement, MetricResult, VerificationResult

class QualityEvaluator:
    def evaluate(self, elements: List[CodeElement]) -> List[VerificationResult]:
        results = []
        for elem in elements:
            metrics = self._evaluate_element(elem)
            results.append(VerificationResult(element=elem, metrics=metrics))
        return results
        
    def _evaluate_element(self, element: CodeElement) -> MetricResult:
        has_doc = element.documentation is not None
        coverage = 1.0 if has_doc else 0.0
        
        if not has_doc:
            return MetricResult(
                coverage=0.0,
                completeness=0.0,
                coherence=0.0,
                readability=0.0,
                issues=["Missing documentation completely."]
            )
            
        doc = element.documentation
        issues = []
        
        # Completeness
        completeness_score = 0.0
        required_elements = 1 # description
        present_elements = 0
        
        if doc.description:
            present_elements += 1
        else:
            issues.append("Missing description.")
            
        if element.parameters:
            required_elements += len(element.parameters)
            doc_param_names = [p.name for p in doc.parameters]
            for param in element.parameters:
                if param in doc_param_names:
                    present_elements += 1
                else:
                    issues.append(f"Parameter '{param}' is not documented.")
                    
        if element.has_return:
            required_elements += 1
            if doc.returns:
                present_elements += 1
            else:
                issues.append("Return value is not documented.")
                
        completeness = present_elements / required_elements if required_elements > 0 else 1.0
        
        # Coherence
        coherence_score = 1.0
        if element.parameters:
            doc_param_names = [p.name for p in doc.parameters]
            for doc_p in doc_param_names:
                if doc_p not in element.parameters:
                    issues.append(f"Documented parameter '{doc_p}' does not exist in code.")
                    coherence_score -= (1.0 / max(1, len(doc_param_names)))
                    
        coherence_score = max(0.0, coherence_score)
        
        # Readability (simple heuristic based on description length and words)
        words = len(doc.description.split())
        readability = min(1.0, words / 10.0) # Assume 10 words is good enough for a basic description
        if words < 3:
            issues.append("Description is too short, poor readability.")
            
        return MetricResult(
            coverage=coverage,
            completeness=completeness,
            coherence=coherence_score,
            readability=readability,
            issues=issues
        )
