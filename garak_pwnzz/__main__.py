"""Command-line entry point for the PwnzzAI Garak suite.

    python -m garak_pwnzz list                 # show plugins, suites, endpoints
    python -m garak_pwnzz preflight            # check the lab is up and reachable
    python -m garak_pwnzz run <suite>|all      # run garak over a suite
    python -m garak_pwnzz analyze              # build tables + figures from runs

This wrapper never reimplements scanning. ``run`` hands each task to garak; the
artifacts it produces are garak's own. Everything here is orchestration and
reporting around that.
"""

from __future__ import annotations

import argparse
import json
import sys

from garak_pwnzz import bootstrap, runner, settings, suites, target_facts


def _cmd_list(_args: argparse.Namespace) -> int:
    """List the contributed plugins, the suites, and the target endpoints.

    Takes the parsed namespace it does not read, so every subcommand handler
    shares one signature and ``main`` can dispatch through a plain dict.
    """
    specs = bootstrap.plugin_specs()
    print("== garak plugins contributed by this project ==")
    for category, names in specs.items():
        print(f"\n{category}:")
        for name in names:
            print(f"  {name}")

    print("\n== suites ==")
    for name in suites.all_suite_names():
        suite = suites.get_suite(name)
        print(
            f"  {name:22s} [{suite.owasp}] {len(suite.tasks):2d} tasks -- {suite.description}"
        )
    print(f"\n  total tasks: {suites.total_task_count()}")

    print("\n== target endpoints under assessment ==")
    for ep in target_facts.ENDPOINTS:
        print(f"  {ep.method:4s} {ep.path:52s} {ep.owasp}  {ep.family}")
    return 0


def _cmd_preflight(_args: argparse.Namespace) -> int:
    """Check the lab app and Ollama are reachable and the pinned model is present."""
    import requests

    cfg = settings.load()
    print(f"target base_url : {cfg.base_url}")
    print(f"ollama host     : {cfg.ollama_host}")
    print(f"model tag       : {cfg.model_tag}")
    print(f"pinned commit   : {target_facts.PINNED_COMMIT}")
    ok = True
    try:
        r = requests.get(cfg.url("/"), timeout=cfg.timeout_fast)
        print(f"GET /           : {r.status_code}")
    except requests.RequestException as exc:
        print(f"GET /           : UNREACHABLE ({exc})")
        ok = False
    try:
        r = requests.get(f"{cfg.ollama_host}/api/tags", timeout=cfg.timeout_fast)
        tags = [m.get("name") for m in r.json().get("models", [])]
        print(f"ollama /api/tags: {r.status_code}; models={tags}")
        if cfg.model_tag not in tags:
            print(f"  WARNING: pinned model {cfg.model_tag!r} not present")
    except requests.RequestException as exc:
        print(f"ollama /api/tags: UNREACHABLE ({exc})")
        ok = False
    print("preflight:", "OK" if ok else "FAILED")
    return 0 if ok else 1


def _cmd_run(args: argparse.Namespace) -> int:
    """Run one suite (or 'all') through garak."""
    if args.target == "all":
        runner.run_all(quiet=args.quiet)
    else:
        if args.target not in suites.all_suite_names():
            print(
                f"unknown suite {args.target!r}; known: {', '.join(suites.all_suite_names())}"
            )
            return 2
        runner.run_suite(args.target, quiet=args.quiet)
    return 0


def _cmd_analyze(_args: argparse.Namespace) -> int:
    """Build all tables, figures, and the HTML dashboard from existing runs."""
    from garak_pwnzz.analysis import analyze, dashboard

    headline = analyze.run()
    dash = dashboard.build()
    print(json.dumps(headline, indent=2, default=str))
    print(f"\nwrote tables and figures to {settings.ANALYSIS_DIR}")
    print(f"wrote dashboard to {dash}")
    return 0


def _cmd_dashboard(_args: argparse.Namespace) -> int:
    """Rebuild only the HTML dashboard from existing analysis output."""
    from garak_pwnzz.analysis import dashboard

    dash = dashboard.build()
    print(f"wrote dashboard to {dash}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the four subcommands."""
    parser = argparse.ArgumentParser(prog="garak_pwnzz", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list plugins, suites and endpoints")
    sub.add_parser("preflight", help="check the lab and Ollama are reachable")

    run_p = sub.add_parser("run", help="run garak over a suite (or 'all')")
    run_p.add_argument("target", help="suite name or 'all'")
    run_p.add_argument(
        "--quiet",
        action="store_true",
        help="capture garak's console output to a per-task log file",
    )

    sub.add_parser(
        "analyze", help="build tables, figures and dashboard from existing runs"
    )
    sub.add_parser("dashboard", help="(re)build only the HTML dashboard")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the selected subcommand."""
    args = build_parser().parse_args(argv)
    handlers = {
        "list": _cmd_list,
        "preflight": _cmd_preflight,
        "run": _cmd_run,
        "analyze": _cmd_analyze,
        "dashboard": _cmd_dashboard,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
