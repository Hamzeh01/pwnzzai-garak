"""Turn garak's native reports into the tables and figures the write-up needs.

Inputs: the ``garak_runs/<suite>/`` directories, each holding per-task
``report.jsonl`` files and a ``run-manifest.json``. Outputs (under
``garak_analysis/``):

* ``attempts.csv`` -- every attempt, one row, joined to its task and OWASP class.
* ``eval-by-detector.csv`` -- garak's own pass/fail/none counts per
  ``(task, detector)``, with attack-success-rate.
* ``family-summary.csv`` / ``owasp-summary.csv`` -- rolled up by attack family
  and OWASP category, using each probe's *primary* detector as the headline.
* ``detector-agreement.csv`` -- custom ground-truth detector vs the stock garak
  detector vs the application's own oracle, attempt by attempt.
* ``sentiment-doseresponse.csv`` and figures -- the poisoning curves.
* ``summary.json`` -- machine-readable headline numbers.
* ``*.svg`` -- the figures.

Only garak's scores are used for outcomes; this module aggregates, it does not
re-judge.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from garak_pwnzz import mitigations, settings, suites, target_facts
from garak_pwnzz.analysis import charts, report_reader
from garak_pwnzz.analysis.report_reader import AttemptRecord, EvalRecord

#: Detectors that describe a *defence working* rather than an attack succeeding.
#: Excluded from attack-success headlines (still reported separately).
_DEFENSIVE_DETECTORS = {"pwnzz.InputRejected"}

#: The application's own oracle flag in generator notes, per surface.
_APP_ORACLE_KEYS = {
    "/training-data-leak/ollama": "app_has_leakage",
    "/order-access/ollama": "app_has_access_violation",
    "/api/catering-rag/query": "app_unsafe_hint_in_answer",
}


@dataclass
class LoadedSuite:
    """One suite's parsed artifacts: attempts, evals, and the run manifest."""
    name: str
    family: str
    owasp: str
    manifest: dict
    attempts: list[AttemptRecord]
    evals: list[EvalRecord]
    #: report_file -> manifest task entry
    task_by_report: dict[str, dict]


def _probe_primary_detector(probe_spec: str) -> str | None:
    """Look up a probe's primary detector from the loaded plugin class."""

    from garak_pwnzz import bootstrap

    bootstrap.install()
    import importlib

    module = importlib.import_module("garak.probes.pwnzz")
    cls_name = probe_spec.split(".")[-1]
    cls = getattr(module, cls_name, None)
    return getattr(cls, "primary_detector", None) if cls else None


def load_suite(run_dir: Path) -> LoadedSuite | None:
    """Load one suite's attempts, evals, and manifest from its run directory."""
    manifest = report_reader.read_manifest(run_dir)
    if not manifest:
        return None
    attempts: list[AttemptRecord] = []
    evals: list[EvalRecord] = []
    task_by_report: dict[str, dict] = {}
    for task in manifest.get("tasks", []):
        report_file = task.get("report_file")
        if not report_file:
            continue
        path = run_dir / report_file
        if not path.exists():
            continue
        task_by_report[report_file] = task
        attempts.extend(report_reader.read_attempts(path))
        evals.extend(report_reader.read_evals(path))
    return LoadedSuite(
        name=manifest.get("suite", run_dir.name),
        family=manifest.get("family", ""),
        owasp=manifest.get("owasp", ""),
        manifest=manifest,
        attempts=attempts,
        evals=evals,
        task_by_report=task_by_report,
    )


def load_all(runs_dir: Path | None = None) -> list[LoadedSuite]:
    """Load every registered suite that has a run directory."""
    runs_dir = runs_dir or settings.RUNS_DIR
    loaded = []
    for name in suites.all_suite_names():
        run_dir = runs_dir / name
        suite = load_suite(run_dir)
        if suite:
            loaded.append(suite)
    return loaded


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------


def _write_csv(path: Path, header: list[str], rows: list[list[Any]]) -> None:
    """Write header + rows to a CSV file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


def attempts_table(loaded: list[LoadedSuite], out_dir: Path) -> None:
    """Write attempts.csv: one row per generation, joined to task and OWASP class."""
    header = [
        "suite", "family", "owasp", "task", "probe", "surface", "seq", "generation",
        "prompt", "response", "primary_detector", "primary_score",
        "leak_rendering", "latency_s", "http_status",
    ]
    rows: list[list[Any]] = []
    for suite in loaded:
        for att in suite.attempts:
            task = suite.task_by_report.get(att.report, {})
            primary = _probe_primary_detector(att.probe) or ""
            rows.append([
                suite.name,
                suite.family,
                suite.owasp,
                task.get("label", ""),
                att.probe,
                att.surface or "",
                att.seq,
                att.generation,
                att.prompt_text.replace("\n", " ")[:200],
                (att.output_text or "").replace("\n", " ")[:300],
                primary,
                att.score(primary),
                att.notes.get("leak_rendering", ""),
                att.notes.get("latency_s", ""),
                att.notes.get("http_status", ""),
            ])
    _write_csv(out_dir / "attempts.csv", header, rows)


def eval_table(loaded: list[LoadedSuite], out_dir: Path) -> None:
    """Write eval-by-detector.csv from garak's own pass/fail/none counts."""
    header = [
        "suite", "task", "probe", "detector", "passed", "fails", "nones",
        "evaluated", "attack_success_rate",
    ]
    rows: list[list[Any]] = []
    for suite in loaded:
        for ev in suite.evals:
            task = suite.task_by_report.get(ev.report, {})
            asr = ev.attack_success_rate
            rows.append([
                suite.name,
                task.get("label", ""),
                ev.probe,
                ev.detector,
                ev.passed,
                ev.fails,
                ev.nones,
                ev.evaluated,
                "" if asr is None else round(asr, 4),
            ])
    _write_csv(out_dir / "eval-by-detector.csv", header, rows)


def _primary_eval_for_task(suite: LoadedSuite, report_file: str) -> EvalRecord | None:
    """The eval row for a task's *primary* detector."""

    task_evals = [e for e in suite.evals if e.report == report_file]
    if not task_evals:
        return None
    probe = task_evals[0].probe
    primary = _probe_primary_detector(probe)
    for e in task_evals:
        if e.detector == primary:
            return e
    return task_evals[0]


def family_and_owasp_summary(loaded: list[LoadedSuite], out_dir: Path) -> dict:
    """Roll primary-detector outcomes up by family and OWASP category."""

    by_family: dict[str, dict[str, int]] = defaultdict(lambda: {"hits": 0, "evaluated": 0, "nones": 0})
    by_owasp: dict[str, dict[str, int]] = defaultdict(lambda: {"hits": 0, "evaluated": 0, "nones": 0})
    task_rows: list[list[Any]] = []

    for suite in loaded:
        for report_file, task in suite.task_by_report.items():
            ev = _primary_eval_for_task(suite, report_file)
            if ev is None:
                continue
            by_family[suite.family]["hits"] += ev.fails
            by_family[suite.family]["evaluated"] += ev.evaluated
            by_family[suite.family]["nones"] += ev.nones
            by_owasp[suite.owasp]["hits"] += ev.fails
            by_owasp[suite.owasp]["evaluated"] += ev.evaluated
            by_owasp[suite.owasp]["nones"] += ev.nones
            task_rows.append([
                suite.name, task.get("label", ""), suite.family, suite.owasp,
                ev.detector, ev.fails, ev.evaluated,
                "" if ev.attack_success_rate is None else round(ev.attack_success_rate, 4),
                task.get("note", ""),
            ])

    _write_csv(
        out_dir / "task-summary.csv",
        ["suite", "task", "family", "owasp", "primary_detector", "hits",
         "evaluated", "attack_success_rate", "note"],
        task_rows,
    )

    fam_rows = []
    for fam, agg in sorted(by_family.items()):
        asr = agg["hits"] / agg["evaluated"] if agg["evaluated"] else None
        fam_rows.append([fam, agg["hits"], agg["evaluated"], agg["nones"],
                         "" if asr is None else round(asr, 4)])
    _write_csv(out_dir / "family-summary.csv",
               ["family", "hits", "evaluated", "nones", "attack_success_rate"], fam_rows)

    owasp_rows = []
    for owasp, agg in sorted(by_owasp.items()):
        asr = agg["hits"] / agg["evaluated"] if agg["evaluated"] else None
        owasp_rows.append([owasp, target_facts.OWASP_LABELS.get(owasp, owasp),
                           agg["hits"], agg["evaluated"], agg["nones"],
                           "" if asr is None else round(asr, 4)])
    _write_csv(out_dir / "owasp-summary.csv",
               ["owasp", "label", "hits", "evaluated", "nones", "attack_success_rate"],
               owasp_rows)

    return {
        "by_family": {
            f: {**v, "attack_success_rate": (v["hits"] / v["evaluated"] if v["evaluated"] else None)}
            for f, v in by_family.items()
        },
        "by_owasp": {
            o: {**v, "label": target_facts.OWASP_LABELS.get(o, o),
                "attack_success_rate": (v["hits"] / v["evaluated"] if v["evaluated"] else None)}
            for o, v in by_owasp.items()
        },
    }


def detector_agreement(loaded: list[LoadedSuite], out_dir: Path) -> dict:
    """Compare the ground-truth detector with the stock detector and the app oracle.

    For each attempt where more than one signal is available, record the trio so
    the write-up can quantify how often a policy-aware detector and a generic
    one disagree, and how often the application's own flag matches an independent
    check of the same definition.
    """

    header = [
        "suite", "task", "probe", "surface", "primary_detector",
        "primary_score", "stock_detector", "stock_score",
        "app_oracle_key", "app_oracle_value",
    ]
    rows: list[list[Any]] = []
    agree_gt_stock = {"agree": 0, "disagree": 0}
    agree_gt_app = {"agree": 0, "disagree": 0}

    for suite in loaded:
        for att in suite.attempts:
            task = suite.task_by_report.get(att.report, {})
            primary = _probe_primary_detector(att.probe)
            if not primary:
                continue
            p_score = att.score(primary)
            stock = next(
                (d for d in att.detector_results
                 if not d.startswith("pwnzz.") and d != primary),
                None,
            )
            s_score = att.score(stock) if stock else None
            oracle_key = _APP_ORACLE_KEYS.get(att.surface or "")
            oracle_val = att.notes.get(oracle_key) if oracle_key else None

            if p_score is not None and s_score is not None:
                p_hit = p_score >= 0.5
                s_hit = s_score >= 0.5
                agree_gt_stock["agree" if p_hit == s_hit else "disagree"] += 1
            if p_score is not None and oracle_val is not None:
                p_hit = p_score >= 0.5
                agree_gt_app["agree" if p_hit == bool(oracle_val) else "disagree"] += 1

            if stock or oracle_key:
                rows.append([
                    suite.name, task.get("label", ""), att.probe, att.surface or "",
                    primary, p_score, stock or "", s_score,
                    oracle_key or "", oracle_val,
                ])
    _write_csv(out_dir / "detector-agreement.csv", header, rows)
    return {
        "ground_truth_vs_stock": agree_gt_stock,
        "ground_truth_vs_app_oracle": agree_gt_app,
    }


# --------------------------------------------------------------------------
# Poisoning dose-response
# --------------------------------------------------------------------------


def mitigation_matrix(loaded: list[LoadedSuite], out_dir: Path) -> dict:
    """Emit the evidence-linked mitigation matrix, annotated with hit counts.

    Each mitigation names the detector(s) that evidence it; we sum garak's own
    hit counts for those detectors across every run so the recommendation is
    tied to a measured number.
    """

    hits_by_detector: dict[str, int] = defaultdict(int)
    for suite in loaded:
        for ev in suite.evals:
            hits_by_detector[ev.detector] += ev.fails

    rows = mitigations.as_rows()
    header = rows[0] + ["evidence_hits"]
    out_rows = [header]
    per_finding = {}
    for m, row in zip(mitigations.MITIGATIONS, rows[1:]):
        total = sum(hits_by_detector.get(d, 0) for d in m.evidence_detectors)
        out_rows.append(row + [str(total)])
        per_finding[m.finding_id] = {
            "owasp": m.owasp,
            "finding": m.finding,
            "evidence_hits": total,
            "control_layer": m.control_layer,
        }
    _write_csv(out_dir / "mitigations.csv", out_rows[0], out_rows[1:])
    return per_finding


def sentiment_doseresponse(loaded: list[LoadedSuite], out_dir: Path, fig_dir: Path) -> dict:
    """Build the budget-vs-flip curve and the per-prompt confidence curves."""

    suite = next((s for s in loaded if s.name == "data-poisoning"), None)
    if suite is None:
        return {}

    # budget -> list of attempts
    by_budget: dict[int, list[AttemptRecord]] = defaultdict(list)
    for att in suite.attempts:
        if att.notes.get("surface") != "/api/test-poisoned-model":
            continue
        budget = att.notes.get("poison_budget")
        if budget is None:
            continue
        by_budget[int(budget)].append(att)

    if not by_budget:
        return {}

    budgets = sorted(by_budget)
    # Flip rate = fraction of trigger-bearing prompts whose poisoned label != control.
    rows: list[list[Any]] = []
    flip_rate: list[float] = []
    trigger_conf: dict[str, list[float | None]] = defaultdict(list)

    for b in budgets:
        atts = by_budget[b]
        flips = 0
        counted = 0
        for att in atts:
            pois = att.notes.get("poisoned_label")
            ctrl = att.notes.get("control_label")
            conf = att.notes.get("poisoned_confidence")
            prompt = att.prompt_text.strip()
            # Signed confidence toward "positive" for the curve.
            signed = None
            if conf is not None and pois is not None:
                signed = conf if pois == "positive" else 1 - conf
            trigger_conf[prompt[:40]].append(signed)
            rows.append([b, prompt[:60], ctrl, pois,
                         att.notes.get("control_confidence"),
                         att.notes.get("poisoned_confidence"),
                         pois != ctrl if (pois and ctrl) else ""])
            if pois and ctrl:
                counted += 1
                if pois != ctrl:
                    flips += 1
        flip_rate.append(flips / counted if counted else 0.0)

    _write_csv(
        out_dir / "sentiment-doseresponse.csv",
        ["poison_budget", "prompt", "control_label", "poisoned_label",
         "control_confidence", "poisoned_confidence", "flipped"],
        rows,
    )

    # Figure 1: flip rate vs budget.
    fig_dir.mkdir(parents=True, exist_ok=True)
    (fig_dir / "sentiment-flip-rate.svg").write_text(
        charts.line_chart(
            "Sentiment poisoning: label-flip rate vs budget",
            [float(b) for b in budgets],
            [charts.Series("flip rate", flip_rate)],
            x_label="poison comments injected",
            y_label="fraction of prompts flipped",
            y_max=1.0,
        ),
        encoding="utf-8",
    )

    # Figure 2: signed positive-confidence per prompt vs budget.
    series = []
    # Keep only the most informative prompts (those that move).
    for label, vals in trigger_conf.items():
        if any(v is not None for v in vals):
            series.append(charts.Series(label, vals))
    series = series[:4]
    (fig_dir / "sentiment-confidence.svg").write_text(
        charts.line_chart(
            "Sentiment poisoning: P(positive) per prompt vs budget",
            [float(b) for b in budgets],
            series,
            x_label="poison comments injected",
            y_label="confidence toward positive",
            y_max=1.0,
            baseline=0.5,
        ),
        encoding="utf-8",
    )

    return {
        "budgets": budgets,
        "flip_rate": {b: r for b, r in zip(budgets, flip_rate)},
        "min_flip_budget": next(
            (b for b, r in zip(budgets, flip_rate) if r > 0), None
        ),
    }


# --------------------------------------------------------------------------
# Figures for the headline families
# --------------------------------------------------------------------------


def family_figures(loaded: list[LoadedSuite], summary: dict, fig_dir: Path) -> None:
    """Render the per-family bar charts (OWASP, levels, ladder, mitigation)."""
    fig_dir.mkdir(parents=True, exist_ok=True)

    # OWASP attack-success bar chart.
    by_owasp = summary["by_owasp"]
    cats = [f"{o}\n{v['label'][:18]}" for o, v in sorted(by_owasp.items())]
    vals = [v["attack_success_rate"] or 0.0 for _, v in sorted(by_owasp.items())]
    (fig_dir / "owasp-attack-success.svg").write_text(
        charts.grouped_bar_chart(
            "Attack success rate by OWASP LLM category (primary detector)",
            cats,
            [charts.Series("attack success", vals)],
            y_label="attack success rate",
            y_max=1.0,
        ),
        encoding="utf-8",
    )

    # Direct-injection: success rate per persona level.
    direct = next((s for s in loaded if s.name == "direct-injection"), None)
    if direct:
        levels, asrs = [], []
        for report_file, task in sorted(direct.task_by_report.items(),
                                        key=lambda kv: kv[1].get("label", "")):
            ev = _primary_eval_for_task(direct, report_file)
            if ev and ev.attack_success_rate is not None:
                levels.append("L" + task.get("label", "").split("-")[-1])
                asrs.append(ev.attack_success_rate)
        if levels:
            (fig_dir / "direct-levels.svg").write_text(
                charts.grouped_bar_chart(
                    "Direct prompt injection: coupon-leak rate by persona level",
                    levels,
                    [charts.Series("leak rate", asrs)],
                    y_label="coupon-leak rate",
                    y_max=1.0,
                ),
                encoding="utf-8",
            )

    # Guardrail ladder: success rate per stage.
    ladder = next((s for s in loaded if s.name == "guardrail-ladder"), None)
    if ladder:
        stages, asrs = [], []
        for report_file, task in sorted(
            ladder.task_by_report.items(),
            key=lambda kv: int(kv[1].get("label", "ladder-stage-0").split("-")[-1]),
        ):
            ev = _primary_eval_for_task(ladder, report_file)
            if ev and ev.attack_success_rate is not None:
                stages.append("B" + task.get("label", "").split("-")[-1])
                asrs.append(ev.attack_success_rate)
        if stages:
            (fig_dir / "guardrail-ladder.svg").write_text(
                charts.grouped_bar_chart(
                    "Guardrail escalation ladder: bypass rate by stage",
                    stages,
                    [charts.Series("bypass rate", asrs)],
                    y_label="bypass rate",
                    y_max=1.0,
                ),
                encoding="utf-8",
            )

    # Catering RAG mitigation: vulnerable vs hardened.
    poison = next((s for s in loaded if s.name == "data-poisoning"), None)
    if poison:
        modes, asrs = [], []
        for report_file, task in sorted(poison.task_by_report.items()):
            if "catering-poison" not in task.get("label", ""):
                continue
            ev = _primary_eval_for_task(poison, report_file)
            if ev and ev.attack_success_rate is not None:
                modes.append("hardened" if "hardened" in task["label"] else "vulnerable")
                asrs.append(ev.attack_success_rate)
        if modes:
            (fig_dir / "catering-mitigation.svg").write_text(
                charts.grouped_bar_chart(
                    "Catering RAG poisoning: influence rate with mitigation on/off",
                    modes,
                    [charts.Series("influence rate", asrs)],
                    y_label="poison influence rate",
                    y_max=1.0,
                ),
                encoding="utf-8",
            )


# --------------------------------------------------------------------------
# Top-level driver
# --------------------------------------------------------------------------


def run(runs_dir: Path | None = None, out_dir: Path | None = None) -> dict:
    """Build every table, figure, and summary.json from the run directories."""
    loaded = load_all(runs_dir)
    if not loaded:
        raise SystemExit("no garak runs found; run the suites first")
    out_dir = out_dir or settings.ANALYSIS_DIR
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    attempts_table(loaded, out_dir)
    eval_table(loaded, out_dir)
    summary = family_and_owasp_summary(loaded, out_dir)
    agreement = detector_agreement(loaded, out_dir)
    dose = sentiment_doseresponse(loaded, out_dir, fig_dir)
    mitigation_findings = mitigation_matrix(loaded, out_dir)
    family_figures(loaded, summary, fig_dir)

    total_attempts = sum(len(s.attempts) for s in loaded)
    headline = {
        "suites": [s.name for s in loaded],
        "total_attempts": total_attempts,
        "by_family": summary["by_family"],
        "by_owasp": summary["by_owasp"],
        "detector_agreement": agreement,
        "sentiment_doseresponse": dose,
        "mitigations": mitigation_findings,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(headline, indent=2, default=str), encoding="utf-8"
    )
    return headline
