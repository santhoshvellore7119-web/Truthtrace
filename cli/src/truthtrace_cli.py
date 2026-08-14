"""
TruthTrace CLI - Command line interface for the Disinformation & Narrative Intelligence Engine
"""
import typer
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
import time

app = typer.Typer(help="TruthTrace: Disinformation & Narrative Intelligence Engine")
console = Console()

# Configuration
API_BASE_URL = "http://localhost:8000"

@app.command()
def check(
    claim: Optional[str] = typer.Argument(None, help="The claim to analyze"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to analyze instead of claim"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (JSON format)")
):
    """
    Analyze a claim or URL for misinformation and narrative intelligence.
    """
    if not claim and not url:
        console.print("[red]Error: Either a claim or URL must be provided[/red]")
        raise typer.Exit(1)

    # Show analysis started
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Analyzing claim...", total=None)

        # Prepare request
        payload = {}
        if claim:
            payload["claim"] = claim
        if url:
            payload["url"] = url

        # Make API request
        try:
            response = requests.post(f"{API_BASE_URL}/analyze", json=payload)
            response.raise_for_status()
            result = response.json()

            # Simulate processing time for better UX
            time.sleep(1)
            progress.update(task, completed=True)

        except requests.exceptions.RequestException as e:
            progress.update(task, description=f"[red]Error connecting to API: {str(e)}[/red]")
            raise typer.Exit(1)

    # Display results
    display_results(result)

    # Save to file if requested
    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        console.print(f"\n[green]Results saved to {output}[/green]")

def display_results(result: dict):
    """Display analysis results in a formatted way."""

    # Verdict panel
    verdict_colors = {
        "CONFIRMED": "green",
        "MOSTLY TRUE": "green",
        "MISLEADING": "yellow",
        "OUT OF CONTEXT": "yellow",
        "FABRICATED": "red",
        "SATIRE": "blue"
    }
    verdict_color = verdict_colors.get(result.get("verdict", "").upper(), "white")

    verdict_panel = Panel(
        f"[{verdict_color}]{result.get('verdict', 'N/A')}[/{verdict_color}]\n"
        f"Credibility Score: {result.get('credibility_score', 0)}%",
        title="Analysis Verdict",
        border_style=verdict_color
    )
    console.print(verdict_panel)

    # Timeline
    if result.get("timeline"):
        timeline_table = Table(title="Timeline & Provenance")
        timeline_table.add_column("Timestamp", style="cyan")
        timeline_table.add_column("Event", style="magenta")

        for event in result["timeline"]:
            timeline_table.add_row(
                event.get("timestamp", ""),
                event.get("event", "")
            )
        console.print(timeline_table)

    # Patient Zero
    if result.get("patient_zero"):
        pz = result["patient_zero"]
        pz_panel = Panel(
            f"Entity: {pz.get('entity', 'N/A')}\n"
            f"Handle: {pz.get('handle', 'N/A')}\n"
            f"Platform: {pz.get('platform', 'N/A')}\n"
            f"Account Created: {pz.get('account_created', 'N/A')}\n"
            f"Bio: {pz.get('bio', 'N/A')}\n"
            f"Network Affiliations: {', '.join(pz.get('network_affiliations', []))}",
            title="Patient Zero & Origin Profile",
            border_style="blue"
        )
        console.print(pz_panel)

    # Source Tweaking
    if result.get("source_tweaking"):
        st = result["source_tweaking"]
        tweak_panel = Panel(
            f"[green]Original Statement:[/green]\n{st.get('original_statement', 'N/A')}\n\n"
            f"[red]Claimed Statement:[/red]\n{st.get('claimed_statement', 'N/A')}\n\n"
            f"[yellow]Alterations Detected:[/yellow]\n" +
            "\n".join([f"• {alt}" for alt in st.get('alterations', [])]),
            title="Source Tweaking Analysis",
            border_style="yellow"
        )
        console.print(tweak_panel)

    # Narrative & Intention
    if result.get("narrative_intention"):
        ni = result["narrative_intention"]
        ni_panel = Panel(
            f"Core Narrative: {ni.get('core_narrative', 'N/A')}\n"
            f"Emotional Hooks: {', '.join(ni.get('emotional_hooks', []))}\n"
            f"Target Demographic: {ni.get('target_demographic', 'N/A')}\n"
            f"Plausible Intent: {ni.get('plausible_intent', 'N/A')}",
            title="Narrative & Intention Matrix",
            border_style="purple"
        )
        console.print(ni_panel)

    # Evidence
    if result.get("evidence"):
        evidence_table = Table(title="Evidence & Sources")
        evidence_table.add_column("Source", style="cyan")
        evidence_table.add_column("URL", style="blue")
        evidence_table.add_column("Timestamp", style="magenta")

        for evidence in result["evidence"]:
            evidence_table.add_row(
                evidence.get("source", ""),
                evidence.get("url", ""),
                evidence.get("timestamp", "")
            )
        console.print(evidence_table)

@app.command()
def health():
    """Check if the TruthTrace API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            console.print("[green]��✓ API is healthy and running[/green]")
        else:
            console.print(f"[red]��✗ API returned status code: {response.status_code}[/red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red]��✗ Cannot connect to API: {str(e)}[/red]")
        console.print("[yellow]Make sure the backend server is running on http://localhost:8000[/yellow]")

if __name__ == "__main__":
    app()