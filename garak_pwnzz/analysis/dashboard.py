"""Build a single self-contained HTML dashboard from the analysis outputs.

The dashboard embeds the generated SVG figures and the headline tables inline
(no external files, no scripts, no network) so it opens straight from disk and
survives being moved into a submission archive. It is generated from
``summary.json`` and the CSV tables produced by :mod:`analyze`, so it always
reflects the latest run.
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from garak_pwnzz import settings, target_facts


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV into a list of dict rows, or [] if missing."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _esc(value: object) -> str:
    """HTML-escape a value for safe inclusion in SVG/HTML text."""
    return html.escape(str(value))


def _pct(value: object) -> str:
    """Format a 0-1 fraction as a percentage string, or an em dash."""
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _svg_inline(path: Path) -> str:
    """Return an SVG file's contents for inline embedding, or a placeholder."""
    if not path.exists():
        return "<p class='muted'>figure not generated</p>"
    return path.read_text(encoding="utf-8")


def _table(rows: list[list[str]], header: list[str]) -> str:
    """Render header + rows as an HTML table."""
    out = ["<table><thead><tr>"]
    out += [f"<th>{_esc(h)}</th>" for h in header]
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
       color: #0f172a; background: #f8fafc; line-height: 1.5; }
@media (prefers-color-scheme: dark) {
  body { color: #e2e8f0; background: #0f172a; }
  .card, header, .fig { background: #1e293b !important; border-color: #334155 !important; }
  th { background: #334155 !important; }
  td, th { border-color: #334155 !important; }
  .muted { color: #94a3b8 !important; }
  svg rect[fill='white'] { fill: #1e293b; }
}
header { background: #fff; border-bottom: 1px solid #e2e8f0; padding: 28px 32px; }
h1 { margin: 0 0 6px; font-size: 24px; }
.sub { color: #64748b; font-size: 14px; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 32px 64px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px 20px; }
.kpi { font-size: 30px; font-weight: 700; }
.kpi-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: .04em; }
h2 { margin: 32px 0 12px; font-size: 18px; border-left: 4px solid #2563eb; padding-left: 10px; }
.muted { color: #64748b; font-size: 13px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 8px 0; overflow-x: auto; display: block; }
th, td { border: 1px solid #e2e8f0; padding: 6px 10px; text-align: left; white-space: nowrap; }
th { background: #f1f5f9; font-weight: 600; }
.fig { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin: 12px 0; overflow-x: auto; }
.fig svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 820px) { .two { grid-template-columns: 1fr; } }
.pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px;
        background: #dbeafe; color: #1e40af; }
"""


def build(analysis_dir: Path | None = None) -> Path:
    """Build the self-contained dashboard.html from the analysis outputs."""
    analysis_dir = analysis_dir or settings.ANALYSIS_DIR
    fig = analysis_dir / "figures"
    summary_path = analysis_dir / "summary.json"
    if not summary_path.exists():
        raise SystemExit("run `python -m garak_pwnzz analyze` first")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    owasp_rows = _read_csv(analysis_dir / "owasp-summary.csv")
    task_rows = _read_csv(analysis_dir / "task-summary.csv")
    mit_rows = _read_csv(analysis_dir / "mitigations.csv")
    agree = summary.get("detector_agreement", {})
    gt_stock = agree.get("ground_truth_vs_stock", {})
    gt_app = agree.get("ground_truth_vs_app_oracle", {})

    total_attempts = summary.get("total_attempts", 0)
    n_suites = len(summary.get("suites", []))
    total_hits = sum(int(r["hits"]) for r in owasp_rows) if owasp_rows else 0

    parts: list[str] = []
    parts.append("<header>")
    parts.append("<h1>PwnzzAI × Garak — Security Assessment Dashboard</h1>")
    parts.append(
        f"<div class='sub'>Garak-native assessment of PwnzzAI Shop "
        f"(pinned commit <code>{target_facts.PINNED_COMMIT[:12]}</code>, "
        f"model <code>llama3.2:1b</code>). "
        f"All figures and numbers are generated from Garak's own "
        f"<code>report.jsonl</code>.</div>"
    )
    parts.append("</header><main>")

    # KPI row
    parts.append("<div class='grid'>")
    for label, value in [
        ("Attempts", f"{total_attempts}"),
        ("Suites", f"{n_suites}"),
        ("Confirmed hits", f"{total_hits}"),
        ("Ground-truth vs stock disagreements",
         f"{gt_stock.get('disagree', 0)}/{gt_stock.get('agree', 0) + gt_stock.get('disagree', 0)}"),
    ]:
        parts.append(
            f"<div class='card'><div class='kpi'>{_esc(value)}</div>"
            f"<div class='kpi-label'>{_esc(label)}</div></div>"
        )
    parts.append("</div>")

    # OWASP overview
    parts.append("<h2>Exposure by OWASP LLM Top 10 (2025)</h2>")
    parts.append("<div class='fig'>" + _svg_inline(fig / "owasp-attack-success.svg") + "</div>")
    if owasp_rows:
        rows = [
            [r["owasp"], r["label"], r["hits"], r["evaluated"], _pct(r["attack_success_rate"])]
            for r in owasp_rows
        ]
        parts.append(_table(rows, ["OWASP", "Category", "Hits", "Evaluated", "Attack success"]))

    # Prompt injection figures
    parts.append("<h2>Prompt injection (LLM01)</h2>")
    parts.append("<div class='two'>")
    parts.append("<div class='fig'>" + _svg_inline(fig / "direct-levels.svg") + "</div>")
    parts.append("<div class='fig'>" + _svg_inline(fig / "guardrail-ladder.svg") + "</div>")
    parts.append("</div>")
    parts.append(
        "<p class='muted'>Left: coupon-leak rate falls as the persona hardens "
        "L1→L5. Right: bypass rate per guardrail stage B0→B9, isolating which "
        "defensive layer each technique defeats.</p>"
    )

    # Poisoning
    parts.append("<h2>Data poisoning (LLM04)</h2>")
    parts.append("<div class='two'>")
    parts.append("<div class='fig'>" + _svg_inline(fig / "sentiment-flip-rate.svg") + "</div>")
    parts.append("<div class='fig'>" + _svg_inline(fig / "catering-mitigation.svg") + "</div>")
    parts.append("</div>")
    dose = summary.get("sentiment_doseresponse", {})
    if dose:
        parts.append(
            f"<p class='muted'>Sentiment backdoor first flips at budget "
            f"<span class='pill'>{_esc(dose.get('min_flip_budget'))}</span> "
            f"mislabelled comments. Right: the catering-RAG mitigation reduces but "
            f"does not eliminate poison influence.</p>"
        )

    # Detector agreement -- the paper's thesis, quantified
    parts.append("<h2>Detector agreement — why policy-aware detection matters</h2>")
    parts.append(
        "<p class='muted'>The ground-truth (policy-aware) detectors and the stock "
        "Garak detector answer different questions, so they disagree often. Where "
        "the application ships its own leak oracle, it is cross-checked against an "
        "independent detector.</p>"
    )
    parts.append(_table(
        [
            ["Ground-truth vs stock detector", str(gt_stock.get("agree", 0)), str(gt_stock.get("disagree", 0))],
            ["Ground-truth vs app's own oracle", str(gt_app.get("agree", 0)), str(gt_app.get("disagree", 0))],
        ],
        ["Comparison", "Agree", "Disagree"],
    ))

    # Per-task table
    parts.append("<h2>Per-task results</h2>")
    if task_rows:
        rows = [
            [r["suite"], r["task"], r["owasp"], r["primary_detector"].replace("pwnzz.", ""),
             r["hits"], r["evaluated"], _pct(r["attack_success_rate"])]
            for r in task_rows
        ]
        parts.append(_table(rows, ["Suite", "Task", "OWASP", "Detector", "Hits", "Eval", "ASR"]))

    # Mitigations
    parts.append("<h2>Evidence-linked mitigations</h2>")
    if mit_rows:
        rows = [
            [r["finding_id"], r["owasp"], r["finding"], r["control_layer"], r.get("evidence_hits", "")]
            for r in mit_rows
        ]
        parts.append(_table(rows, ["ID", "OWASP", "Finding", "Control layer", "Evidence hits"]))
    parts.append(
        "<p class='muted'>Full controls and residual-risk notes in "
        "<code>garak_analysis/mitigations.csv</code> and "
        "<code>docs/05-results-and-mitigations.md</code>.</p>"
    )

    parts.append(
        "<p class='muted' style='margin-top:40px'>Generated by "
        "<code>python -m garak_pwnzz dashboard</code>. Individual Garak HTML "
        "reports are under <code>garak_runs/&lt;suite&gt;/&lt;task&gt;.report.html</code>.</p>"
    )
    parts.append("</main>")

    doc = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>PwnzzAI × Garak — Dashboard</title>"
        f"<style>{_CSS}</style></head><body>"
        + "".join(parts)
        + "</body></html>"
    )
    out = analysis_dir / "dashboard.html"
    out.write_text(doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
