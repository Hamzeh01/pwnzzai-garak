"""Parse garak ``report.jsonl`` files into plain Python records.

Garak writes a JSONL stream of typed entries. The two this project reads are:

* ``attempt`` (status 2 = complete): one prompt, its outputs, per-detector
  scores, and the per-response ``notes`` our generators attached.
* ``eval``: garak's own aggregate for one ``(probe, detector)`` pair --
  ``passed`` / ``fails`` / ``nones`` / ``total``. These are authoritative; the
  analysis reports them rather than recomputing from attempts.

Nothing here interprets a score. It only reshapes garak's output into rows that
:mod:`garak_pwnzz.analysis.analyze` can tabulate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass
class AttemptRecord:
    """One generation within a completed garak attempt, flattened.

    Garak runs ``generations`` samples per prompt and stores them as parallel
    lists (``outputs`` / ``conversations`` / each detector's score list). One
    ``AttemptRecord`` corresponds to one generation, so a probe with 12 prompts
    at 3 generations yields 36 records -- matching garak's own
    ``total_evaluated``.
    """

    report: str
    probe: str
    goal: str
    seq: int
    generation: int
    prompt_text: str
    output_text: str | None
    detector_results: dict[str, float | None]
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def surface(self) -> str | None:
        return self.notes.get("surface")

    def score(self, detector: str) -> float | None:
        return self.detector_results.get(detector)


@dataclass
class EvalRecord:
    """Garak's own aggregate for one (probe, detector) pair."""

    report: str
    probe: str
    detector: str
    passed: int
    fails: int
    nones: int
    total: int

    @property
    def evaluated(self) -> int:
        """Attempts that produced a non-None score."""

        return self.passed + self.fails

    @property
    def attack_success_rate(self) -> float | None:
        """Fraction of *evaluated* attempts that were hits (fails, in garak terms)."""

        if self.evaluated == 0:
            return None
        return self.fails / self.evaluated


def _generation_outputs(attempt: dict) -> list[tuple[str | None, dict]]:
    """Return ``(text, notes)`` for every generation, in order.

    Prefer the ``conversations`` list -- each assistant turn carries the
    generator notes. Fall back to the flat ``outputs`` list, which has text but
    no notes.
    """

    results: list[tuple[str | None, dict]] = []
    for conv in attempt.get("conversations") or []:
        text, notes = None, {}
        for turn in conv.get("turns", []):
            if turn.get("role") == "assistant":
                content = turn.get("content") or {}
                text, notes = content.get("text"), content.get("notes") or {}
        results.append((text, notes))
    if results:
        return results
    for out in attempt.get("outputs") or []:
        if isinstance(out, dict):
            results.append((out.get("text"), out.get("notes") or {}))
        elif isinstance(out, str):
            results.append((out, {}))
    return results


def _first_user_prompt(attempt: dict) -> str:
    conversations = attempt.get("conversations") or []
    for conv in conversations:
        for turn in conv.get("turns", []):
            if turn.get("role") == "user":
                return (turn.get("content") or {}).get("text", "")
    prompt = attempt.get("prompt")
    if isinstance(prompt, dict):
        turns = prompt.get("turns", [])
        if turns:
            return (turns[0].get("content") or {}).get("text", "")
    return ""


def iter_report(path: Path) -> Iterator[dict]:
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def read_attempts(path: Path) -> list[AttemptRecord]:
    name = path.name
    records: list[AttemptRecord] = []
    for entry in iter_report(path):
        if entry.get("entry_type") != "attempt" or entry.get("status") != 2:
            continue
        prompt_text = _first_user_prompt(entry)
        generations = _generation_outputs(entry)
        det_results = entry.get("detector_results", {})
        for gi, (text, notes) in enumerate(generations):
            # Slice each detector's parallel score list to this generation.
            per_gen = {
                det: (scores[gi] if isinstance(scores, list) and gi < len(scores) else None)
                for det, scores in det_results.items()
            }
            records.append(
                AttemptRecord(
                    report=name,
                    probe=entry.get("probe_classname", ""),
                    goal=entry.get("goal", ""),
                    seq=entry.get("seq", -1),
                    generation=gi,
                    prompt_text=prompt_text,
                    output_text=text,
                    detector_results=per_gen,
                    notes=notes,
                )
            )
    return records


def read_evals(path: Path) -> list[EvalRecord]:
    name = path.name
    records: list[EvalRecord] = []
    for entry in iter_report(path):
        if entry.get("entry_type") != "eval":
            continue
        passed = int(entry.get("passed", 0))
        fails = int(entry.get("fails", 0))
        nones = int(entry.get("nones", 0))
        total = int(entry.get("total_evaluated", passed + fails + nones))
        records.append(
            EvalRecord(
                report=name,
                probe=entry.get("probe", ""),
                detector=entry.get("detector", ""),
                passed=passed,
                fails=fails,
                nones=nones,
                total=total,
            )
        )
    return records


def read_manifest(run_dir: Path) -> dict:
    manifest_path = run_dir / "run-manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def label_for_report(run_dir: Path, report_name: str) -> dict:
    """Return the manifest task entry whose report matches ``report_name``."""

    manifest = read_manifest(run_dir)
    for task in manifest.get("tasks", []):
        if task.get("report_file") == report_name:
            return task
    return {}
