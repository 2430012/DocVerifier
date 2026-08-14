from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import traceback

from src.parsers import get_parser
from src.metrics.evaluator import QualityEvaluator
from src.semantic.verifier import SemanticVerifier

app = FastAPI(title="DocVerifier API")

# Initialize global verifier
semantic_verifier = None

class MetricData(BaseModel):
    coverage: float
    completeness: float
    coherence: float
    readability: float
    semantic_similarity: Optional[float] = None
    issues: List[str]

class ResultData(BaseModel):
    file_name: str
    element: str
    type: str
    line: int
    metrics: MetricData

@app.post("/api/verify", response_model=List[ResultData])
async def verify_code(
    files: List[UploadFile] = File(...),
    language: str = Form(...),
    semantic: bool = Form(False)
):
    output = []
    
    global semantic_verifier
    if semantic and semantic_verifier is None:
        semantic_verifier = SemanticVerifier()
        
    evaluator = QualityEvaluator()

    for file in files:
        try:
            content = await file.read()
            source_code = content.decode("utf-8")
        except Exception as e:
            continue
            
        try:
            lang_parser = get_parser(language)
            elements = lang_parser.parse(source_code)
            results = evaluator.evaluate(elements)
            
            if semantic:
                semantic_verifier.verify(results)
                
            for res in results:
                output.append(ResultData(
                    file_name=file.filename,
                    element=res.element.name,
                    type=res.element.type,
                    line=res.element.start_line,
                    metrics=MetricData(
                        coverage=res.metrics.coverage,
                        completeness=res.metrics.completeness,
                        coherence=res.metrics.coherence,
                        readability=res.metrics.readability,
                        semantic_similarity=res.metrics.semantic_similarity,
                        issues=res.metrics.issues
                    )
                ))
        except Exception as e:
            traceback.print_exc()
            output.append(ResultData(
                file_name=file.filename if hasattr(file, 'filename') else "Archivo",
                element="ERROR PARSER",
                type="Error",
                line=0,
                metrics=MetricData(
                    coverage=0.0,
                    completeness=0.0,
                    coherence=0.0,
                    readability=0.0,
                    semantic_similarity=None,
                    issues=[f"Error al procesar: {str(e)}"]
                )
            ))
            
    return output

# Serve Static files (the Web App)
web_dir = os.path.join(os.path.dirname(__file__), "web")
app.mount("/static", StaticFiles(directory=web_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(web_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
