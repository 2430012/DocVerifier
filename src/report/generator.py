from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import json
import os
from ..models import VerificationResult

class ReportGenerator:
    def __init__(self):
        self.console = Console()

    def generate_cli_report(self, results: List[VerificationResult], file_path: str):
        self.console.print(f"\n[bold blue]Documentation Verification Report for:[/bold blue] {file_path}")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Element", style="dim", width=20)
        table.add_column("Type", justify="center")
        table.add_column("Coverage", justify="center")
        table.add_column("Completeness", justify="center")
        table.add_column("Coherence", justify="center")
        table.add_column("Semantic Score", justify="center")
        table.add_column("Issues", style="red")
        
        overall_cov = 0
        overall_comp = 0
        
        for res in results:
            overall_cov += res.metrics.coverage
            overall_comp += res.metrics.completeness
            
            cov_str = f"{res.metrics.coverage * 100:.0f}%"
            comp_str = f"{res.metrics.completeness * 100:.0f}%"
            coh_str = f"{res.metrics.coherence * 100:.0f}%"
            sem_str = f"{res.metrics.semantic_similarity:.2f}" if res.metrics.semantic_similarity else "N/A"
            
            issues_str = "\n".join(res.metrics.issues) if res.metrics.issues else "[green]None[/green]"
            
            table.add_row(
                res.element.name,
                res.element.type,
                cov_str,
                comp_str,
                coh_str,
                sem_str,
                issues_str
            )
            
        self.console.print(table)
        
        if results:
            avg_cov = overall_cov / len(results)
            avg_comp = overall_comp / len(results)
            
            summary = Text()
            summary.append(f"Total Elements Analyzed: {len(results)}\n", style="bold")
            summary.append(f"Average Coverage: {avg_cov * 100:.1f}%\n", style="bold green" if avg_cov > 0.8 else "bold red")
            summary.append(f"Average Completeness: {avg_comp * 100:.1f}%", style="bold green" if avg_comp > 0.8 else "bold red")
            
            self.console.print(Panel(summary, title="Summary", border_style="blue"))
        else:
            self.console.print("[yellow]No documentable elements found.[/yellow]")

    def generate_json_report(self, results: List[VerificationResult], output_file: str):
        data = []
        for res in results:
            data.append({
                "element": res.element.name,
                "type": res.element.type,
                "line": res.element.start_line,
                "metrics": {
                    "coverage": res.metrics.coverage,
                    "completeness": res.metrics.completeness,
                    "coherence": res.metrics.coherence,
                    "readability": res.metrics.readability,
                    "semantic_similarity": res.metrics.semantic_similarity,
                    "issues": res.metrics.issues
                }
            })
            
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=4)
        self.console.print(f"[green]JSON report saved to {output_file}[/green]")
