#!/bin/bash

# Activar el entorno virtual
source venv/bin/activate

# Ejecutar el servidor web de FastAPI con uvicorn
echo "Iniciando DocVerifier Web UI..."
echo "Abre tu navegador web en: http://localhost:8000"
uvicorn src.api:app --host 0.0.0.0 --port 8000
