# DocVerifier: Verificador de Documentación de Código Fuente

DocVerifier es una herramienta automatizada de análisis estático y procesamiento de lenguaje natural diseñada para evaluar la calidad, cobertura, completitud y coherencia de la documentación (comentarios) en el código fuente.

Soporta los siguientes lenguajes y estándares:
- **Python**: PEP 257 / NumPy / Sphinx
- **Java**: Javadoc
- **C++**: Doxygen
- **Kotlin**: KDoc

## Características Principales
1. **Análisis Léxico-Sintáctico**: Parsea la estructura del código utilizando Abstract Syntax Trees (AST) a través de `tree-sitter`.
2. **Evaluación de Métricas**:
   - **Cobertura**: Porcentaje de clases y métodos documentados.
   - **Completitud**: Verificación de presencia de descripciones, parámetros (`@param`), valores de retorno (`@return`) y excepciones.
   - **Coherencia**: Detección de inconsistencias entre los parámetros documentados y la firma real de la función.
   - **Legibilidad**: Evaluación heurística básica basada en longitud y estructura del comentario.
3. **Verificación Semántica (NLP)**: Utiliza **CodeBERT** (mediante `transformers` de HuggingFace) para evaluar la similitud semántica entre el código implementado y la descripción en texto natural.
4. **Reportes accionables**: Interfaz de línea de comandos (CLI) rica con `rich` y exportación a JSON para integración CI/CD.

## Instalación

1. Clona el repositorio y navega a la carpeta.
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

*Nota: La primera vez que se ejecute la verificación semántica, descargará automáticamente el modelo CodeBERT.*

## Uso

### Verificación básica por CLI

Para analizar un archivo y ver un reporte detallado en la consola:

```bash
# Python
python src/main.py examples/example.py -l python

# Java
python src/main.py examples/example.java -l java

# C++
python src/main.py examples/example.cpp -l cpp

# Kotlin
python src/main.py examples/example.kt -l kotlin
```

### Habilitar Verificación Semántica (CodeBERT)

Añade el flag `--semantic` o `-s` para que el sistema utilice Inteligencia Artificial (CodeBERT) y detecte si el comentario y el código fuente no coinciden en significado.

```bash
python src/main.py examples/example.java -l java --semantic
```

### Exportar a JSON (Integración CI/CD)

Para pipelines automatizados, puedes exportar el resultado a JSON utilizando el flag `--format json` y especificando un archivo de salida con `--output`.

```bash
python src/main.py examples/example.py -l python --format json --output report.json
```

## Integración CI/CD (Ejemplo GitHub Actions)

Puedes integrar fácilmente esta herramienta en tu flujo de CI/CD:

```yaml
name: "Verificar Documentación"
on: [push, pull_request]

jobs:
  verify-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: pip install -r requirements.txt
        
      - name: Verify Documentation (Python)
        run: python src/main.py main_module.py -l python --format json --output report.json
        
      - name: Enforce Coverage
        run: |
          # Ejemplo simple: usar jq para fallar el build si hay poca cobertura
          # apt-get install jq
          COVERAGE=$(jq '[.[].metrics.coverage] | add / length' report.json)
          echo "Coverage: $COVERAGE"
          # Lógica para fallar si $COVERAGE < 0.8
```

## Arquitectura

El sistema se compone de varios módulos:
- `parsers/`: Contiene los analizadores léxicos para extraer información del AST para cada lenguaje apoyados en `tree-sitter`.
- `metrics/`: Contiene la lógica matemática para evaluar completitud y coherencia.
- `semantic/`: Integra modelos de Hugging Face para embeddings de código y texto.
- `report/`: Genera la salida final (CLI o JSON).
