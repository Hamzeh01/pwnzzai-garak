"""Drive garak once per task and collect the native artifacts.

Each task becomes a real garak invocation through ``garak.cli.main`` with a
generated config file -- the same entry point a human would use. Nothing about
the scan is reimplemented here: garak owns prompt sequencing, detector
execution, ``report.jsonl`` / ``hitlog.jsonl`` / ``report.html`` generation, and
scoring. This module only decides *what* to run and *where* the outputs land,
then writes a manifest tying the run together.

The generated per-task config files are kept. They are the reproduction
instructions in executable form: ``python -m garak --config <file>`` re-runs any
single task exactly.
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from garak_pwnzz import bootstrap, settings, suites, target_facts
from garak_pwnzz.garak_plugins.probes.pwnzz import PROBE_TARGET_GENERATOR


def _ensure_utf8_stdout() -> None:
    """Garak prints emoji; a cp1252 console would crash on them."""

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


def _validate_pairing(task: suites.Task) -> None:
    """Refuse a probe/generator pairing the probes module says is wrong."""

    probe_class = task.probe.split(".")[-1]
    generator_class = task.generator.split(".")[-1]
    expected = PROBE_TARGET_GENERATOR.get(probe_class)
    if expected and generator_class not in expected:
        raise ValueError(
            f"task {task.label!r}: probe {probe_class} targets one of {expected}, "
            f"not {generator_class}"
        )


def _build_config(task: suites.Task, cfg: settings.Settings, report_dir: Path) -> dict:
    """Compose the garak run config for one task."""

    generator_class = task.generator.split(".")[-1]
    generator_config = {
        # Give every surface the connection facts explicitly so a config file
        # is self-contained and reproducible without the environment.
        "base_url": cfg.base_url,
        **task.generator_config,
    }
    return {
        "run": {
            "generations": task.generations,
            # Seeds garak's own RNG (prompt sampling, buff order). The Ollama
            # model behind the app is not seedable through this path, so the
            # analysis reports variation across generations rather than assuming
            # determinism.
            "seed": 20260805,
        },
        "system": {
            "parallel_attempts": False,
            "parallel_requests": False,
            "lite": False,
            "verbose": 0,
        },
        "plugins": {
            # The class must be named in target_type; target_name is only a
            # free-text model label. "pwnzz" alone would load the module's
            # DEFAULT_CLASS instead of the surface this task wants.
            "target_type": task.generator,  # e.g. "pwnzz.SentimentClassifier"
            "target_name": f"{generator_class}::{task.label}",
            "probe_spec": task.probe,
            "extended_detectors": True,
            "generators": {"pwnzz": {generator_class: generator_config}},
        },
        "reporting": {
            "report_dir": str(report_dir),
            "report_prefix": task.label,
        },
    }


def run_task(
    task: suites.Task,
    cfg: settings.Settings,
    run_dir: Path,
    *,
    quiet: bool = False,
) -> dict:
    """Execute one task through garak. Returns a manifest entry."""

    import garak.cli
    from garak._plugins import PluginProvider

    _validate_pairing(task)

    # Garak caches plugin instances by str(config_root). Because every task in a
    # suite is driven through the same global _config in one process, that key is
    # identical across tasks -- so without clearing it, task 2 would silently
    # reuse task 1's generator (e.g. every persona level would rerun level 1).
    # Clear the instance cache so each task builds a fresh generator from its own
    # config. This is the difference between a real level/stage/budget sweep and
    # the same run repeated N times.
    PluginProvider._instance_cache = {}  # pylint: disable=protected-access

    run_dir.mkdir(parents=True, exist_ok=True)
    config = _build_config(task, cfg, run_dir)

    config_path = run_dir / f"{task.label}.config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    argv = ["--config", str(config_path)]

    started = time.time()
    log_buffer = io.StringIO()
    error: str | None = None
    try:
        if quiet:
            with redirect_stdout(log_buffer):
                garak.cli.main(argv)
        else:
            garak.cli.main(argv)
    except SystemExit as exc:  # garak calls sys.exit on some paths
        if exc.code not in (0, None):
            error = f"garak exited with code {exc.code}"
    # Deliberately broad: one task blowing up must not abort the remaining
    # tasks in the suite. The failure is recorded in the manifest entry.
    except Exception as exc:  # pylint: disable=broad-exception-caught
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.time() - started

    report_path = run_dir / f"{task.label}.report.jsonl"
    entry = {
        "label": task.label,
        "probe": task.probe,
        "generator": task.generator,
        "generator_config": task.generator_config,
        "generations": task.generations,
        "note": task.note,
        "config_file": config_path.name,
        "report_file": report_path.name if report_path.exists() else None,
        "hitlog_file": (
            f"{task.label}.hitlog.jsonl"
            if (run_dir / f"{task.label}.hitlog.jsonl").exists()
            else None
        ),
        "html_file": (
            f"{task.label}.report.html"
            if (run_dir / f"{task.label}.report.html").exists()
            else None
        ),
        "elapsed_s": round(elapsed, 2),
        "error": error,
    }
    if quiet:
        (run_dir / f"{task.label}.garak.log").write_text(
            log_buffer.getvalue(), encoding="utf-8"
        )
    return entry


def run_suite(
    suite_name: str,
    *,
    cfg: settings.Settings | None = None,
    quiet: bool = False,
) -> Path:
    """Run every task in a suite. Returns the run directory holding all artifacts."""

    _ensure_utf8_stdout()
    bootstrap.install()
    cfg = cfg or settings.load()
    suite = suites.get_suite(suite_name)

    run_dir = settings.RUNS_DIR / suite_name
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "suite": suite.name,
        "family": suite.family,
        "owasp": suite.owasp,
        "description": suite.description,
        "target": {
            "base_url": cfg.base_url,
            "model_tag": cfg.model_tag,
            "pinned_commit": target_facts.PINNED_COMMIT,
            "pinned_image": target_facts.PINNED_IMAGE_DIGEST,
        },
        # Recorded whether or not the judge ran, so a report always states which
        # signals produced it rather than leaving a reader to infer it from the
        # presence of a column.
        "judge": {
            "enabled": cfg.judge_enabled,
            "model": cfg.judge_model if cfg.judge_enabled else None,
            "shares_weights_with_target": (
                cfg.judge_is_target_model if cfg.judge_enabled else None
            ),
        },
        "tasks": [],
    }

    print(f"\n=== suite: {suite.name} ({len(suite.tasks)} tasks) ===")
    for i, task in enumerate(suite.tasks, 1):
        print(
            f"[{i}/{len(suite.tasks)}] {task.label} :: {task.probe} -> {task.generator}"
        )
        entry = run_task(task, cfg, run_dir, quiet=quiet)
        status = "ok" if entry["error"] is None and entry["report_file"] else "FAILED"
        print(f"      {status} in {entry['elapsed_s']}s")
        manifest["tasks"].append(entry)

    manifest_path = run_dir / "run-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"=== manifest: {manifest_path} ===")
    return run_dir


def run_all(*, cfg: settings.Settings | None = None, quiet: bool = False) -> list[Path]:
    """Run every registered suite."""

    return [run_suite(name, cfg=cfg, quiet=quiet) for name in suites.all_suite_names()]
