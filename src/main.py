import argparse
import sys
import os
from parsers import get_parser
from metrics.evaluator import QualityEvaluator
from semantic.verifier import SemanticVerifier
from report.generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Source Code Documentation Verifier")
    parser.add_argument("file", help="Path to the source file to verify")
    parser.add_argument("--language", "-l", required=True, choices=["python", "java", "cpp", "kotlin"], help="Programming language of the file")
    parser.add_argument("--format", "-f", choices=["cli", "json"], default="cli", help="Output format")
    parser.add_argument("--output", "-o", help="Output file for JSON report")
    parser.add_argument("--semantic", "-s", action="store_true", help="Enable semantic verification with CodeBERT")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
        
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    # 1. Parsing
    try:
        lang_parser = get_parser(args.language)
        elements = lang_parser.parse(source_code)
    except Exception as e:
        print(f"Error during parsing: {e}")
        sys.exit(1)
        
    # 2. Quality Metrics Evaluation
    evaluator = QualityEvaluator()
    results = evaluator.evaluate(elements)
    
    # 3. Semantic Verification
    if args.semantic:
        verifier = SemanticVerifier()
        verifier.verify(results)
        
    # 4. Report Generation
    report_gen = ReportGenerator()
    if args.format == "json":
        output_file = args.output or "report.json"
        report_gen.generate_json_report(results, output_file)
    else:
        report_gen.generate_cli_report(results, args.file)

if __name__ == "__main__":
    main()
