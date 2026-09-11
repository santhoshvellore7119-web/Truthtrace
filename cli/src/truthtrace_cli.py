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
    """Display analysis results in a formatted way matching the Dossier schema."""

    # Verdict panel
    verdict_colors = {
        "TRUE": "green",
        "CONFIRMED": "green",
        "MOSTLY TRUE": "green",
        "MISLEADING": "yellow",
        "OUT OF CONTEXT": "yellow",
        "FALSE": "red",
        "FABRICATED": "red",
        "SATIRE": "blue",
        "UNVERIFIED": "magenta"
    }
    raw_verdict = result.get("overall_verdict") or result.get("verdict") or "UNVERIFIED"
    verdict_str = raw_verdict.upper()
    verdict_color = verdict_colors.get(verdict_str, "white")

    raw_conf = result.get("overall_confidence")
    if raw_conf is None:
        raw_conf = result.get("credibility_score", 0.5)
        if raw_conf > 1.0:
            raw_conf = raw_conf / 100.0
    conf_pct = int(float(raw_conf) * 100)

    verdict_panel = Panel(
        f"[bold {verdict_color}]{verdict_str}[/bold {verdict_color}]\n"
        f"Forensic Confidence: {conf_pct}%\n"
        f"Analyzed Claim: [italic]{result.get('input_claim', 'N/A')}[/italic]",
        title="Forensic Verdict & Credibility Assessment",
        border_style=verdict_color
    )
    console.print(verdict_panel)

    # Patient Zero & Earliest Origin
    if result.get("patient_zero"):
        pz = result["patient_zero"]
        pz_panel = Panel(
            f"Platform: {pz.get('platform', 'N/A')}\n"
            f"Originating Handle / Domain: [bold cyan]{pz.get('handle', 'N/A')}[/bold cyan]\n"
            f"First Discovered At: {pz.get('first_seen_at', 'N/A')}\n"
            f"Prior Flagged Claims: {pz.get('prior_flagged_claims', 0)}",
            title="Candidate Patient Zero & Origin Profile",
            border_style="cyan"
        )
        console.print(pz_panel)

    # Narrative & Intention Matrix
    narrative = result.get("narrative") or result.get("narrative_intention")
    if narrative:
        hooks = narrative.get('emotional_hooks', [])
        hooks_str = ', '.join(hooks) if isinstance(hooks, list) else str(hooks)
        ni_panel = Panel(
            f"Core Narrative: [bold]{narrative.get('core_narrative', 'N/A')}[/bold]\n"
            f"Emotional Hooks: {hooks_str}\n"
            f"Target Demographic: {narrative.get('target_demographic', 'N/A')}\n"
            f"Plausible Intent: {narrative.get('plausible_intent', 'N/A')}",
            title="Narrative & Motive Intelligence Matrix",
            border_style="magenta"
        )
        console.print(ni_panel)

    # Timeline & Provenance Propagation
    timeline = result.get("timeline", [])
    if timeline:
        timeline_table = Table(title="Chronological Provenance Timeline")
        timeline_table.add_column("Timestamp / Earliest CDX", style="cyan", no_wrap=True)
        timeline_table.add_column("Source / Platform", style="green")
        timeline_table.add_column("Title / Discovered Event", style="white")
        timeline_table.add_column("Credibility", style="yellow")

        for event in timeline:
            ts = event.get("earliest_cdx_timestamp") or event.get("timestamp") or "N/A"
            timeline_table.add_row(
                str(ts)[:19],
                event.get("source", "Web"),
                (event.get("title") or event.get("event") or "")[:70],
                event.get("credibility_tier", "unverified")
            )
        console.print(timeline_table)

    # Discovered Evidence & Fact-Checking Sources
    evidence_list = []
    for sub in result.get("sub_claims", []):
        for ev in sub.get("evidence", []):
            evidence_list.append(ev)

    if evidence_list:
        evidence_table = Table(title="Corroborating & Registry Evidence")
        evidence_table.add_column("Domain / Source", style="cyan")
        evidence_table.add_column("URL", style="blue")
        evidence_table.add_column("Tier", style="magenta")

        for ev in evidence_list[:8]:
            src = ev.get("source", {})
            evidence_table.add_row(
                src.get("domain", "web"),
                src.get("url", ""),
                src.get("credibility_tier", "unverified")
            )
        console.print(evidence_table)

    # Cross-Investigation Memory & Episodic Recall
    cross_mem = result.get("cross_investigation_memory", [])
    if cross_mem:
        console.print(f"\n[bold green][MEM][/bold green] Episodic Learning Memory Match: Found {len(cross_mem)} related historical investigations.")

@app.command()
def health():
    """Check if the TruthTrace API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            console.print("[green][OK] API is healthy and running[/green]")
        else:
            console.print(f"[red][ERR] API returned status code: {response.status_code}[/red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red][ERR] Cannot connect to API: {str(e)}[/red]")
        console.print("[yellow]Make sure the backend server is running on http://localhost:8000[/yellow]")

if __name__ == "__main__":
    app()