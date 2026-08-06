"""Run the LLM-as-judge over every row of attempts.csv and write a new CSV
with the judge's verdict, reasoning, and raw output appended as columns.

Usage:
    python judge_attempts.py --input attempts.csv --output attempts_with_judge.csv
    python judge_attempts.py --input attempts.csv --output attempts_with_judge.csv --dry-run
    python judge_attempts.py --resume   # continues an interrupted real run
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from judge.criteria import get_criteria
from judge.prompts import JUDGE_SYSTEM_PROMPT, build_user_prompt
from judge.verdict import parse_judge_response

JUDGE_MODEL = "llama3.2:latest"
JUDGE_HOST = "http://127.0.0.1:11434"

EXTRA_FIELDS = [
    "row_index",
    "judge_verdict",
    "judge_reasoning",
    "judge_matches_primary_score",
    "judge_confidence_note",
    "judge_raw",
]


def build_context_prefixed_prompt(row: dict, criteria) -> str:
    """Attach the row's own metadata as context on top of the scenario-specific prompt."""

    context = (
        f"SUITE: {row.get('suite', '')}\n"
        f"FAMILY: {row.get('family', '')}\n"
        f"OWASP CATEGORY: {row.get('owasp', '')}\n"
        f"TASK: {row.get('task', '')}\n"
        f"PROBE: {row.get('probe', '')}\n"
    )
    user_prompt = build_user_prompt(
        attack_prompt=row.get("prompt", ""),
        model_response=row.get("response", ""),
        attack_criteria=criteria.attack_criteria,
        expected_output=criteria.expected_output,
    )
    return f"{context}\n{user_prompt}"


def compute_agreement(primary_score: str, judge_label: str) -> str:
    """Return 'True'/'False' if comparable, else '' (e.g. missing score)."""

    try:
        primary_bool = float(primary_score) >= 0.5
    except (TypeError, ValueError):
        return ""
    judge_bool = judge_label == "success"
    return str(primary_bool == judge_bool)


def load_already_judged_indices(output_path: Path) -> set[int]:
    if not output_path.exists():
        return set()
    with output_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {int(row["row_index"]) for row in reader if row.get("row_index")}


def run(
    input_path: Path,
    output_path: Path,
    *,
    dry_run: bool,
    resume: bool,
    delay_seconds: float,
) -> None:
    with input_path.open("r", encoding="utf-8-sig", newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fieldnames = fieldnames + [f for f in EXTRA_FIELDS if f not in fieldnames]

    already_judged = load_already_judged_indices(output_path) if resume else set()
    file_mode = "a" if resume and already_judged else "w"
    write_header = not (resume and already_judged)

    judge = None
    if not dry_run:
        from judge.ollama import OllamaJudge  # imported lazily so --dry-run needs no ollama package

        judge = OllamaJudge(model=JUDGE_MODEL, host=JUDGE_HOST)

    total = len(rows)
    with output_path.open(file_mode, encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=out_fieldnames)
        if write_header:
            writer.writeheader()

        for i, row in enumerate(rows, start=1):
            if i in already_judged:
                continue

            row["row_index"] = str(i)
            criteria = get_criteria(row.get("probe", ""))
            row["judge_confidence_note"] = criteria.confidence_note

            if dry_run:
                row["judge_verdict"] = "ambiguous"
                row["judge_reasoning"] = "(dry run - judge not called)"
                row["judge_matches_primary_score"] = ""
                row["judge_raw"] = ""
            else:
                user_prompt = build_context_prefixed_prompt(row, criteria)
                raw = judge.judge(system_prompt=JUDGE_SYSTEM_PROMPT, user_prompt=user_prompt)
                verdict = parse_judge_response(raw)

                row["judge_verdict"] = verdict.label
                row["judge_reasoning"] = verdict.reasoning
                row["judge_matches_primary_score"] = compute_agreement(
                    row.get("primary_score", ""), verdict.label
                )
                row["judge_raw"] = raw.replace("\n", " ")
                time.sleep(delay_seconds)

            writer.writerow(row)
            outfile.flush()  # so a crash/interrupt doesn't lose progress
            print(
                f"[{i}/{total}] {row.get('probe', '')} "
                f"seq={row.get('seq', '')} gen={row.get('generation', '')} "
                f"-> {row['judge_verdict']}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="attempts.csv")
    parser.add_argument("--output", default="attempts_with_judge.csv")
    parser.add_argument("--dry-run", action="store_true", help="skip Ollama calls, test the pipeline only")
    parser.add_argument("--resume", action="store_true", help="continue an interrupted real run")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds between judge calls")
    args = parser.parse_args()
    run(
        Path(args.input),
        Path(args.output),
        dry_run=args.dry_run,
        resume=args.resume,
        delay_seconds=args.delay,
    )
