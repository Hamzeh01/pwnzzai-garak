"""Garak-native security assessment suite for the PwnzzAI Shop application.

This package is a set of first-class Garak plugins -- generators, probes and
detectors -- plus the run/analysis tooling around them. Everything that touches
the target goes through Garak, so every run produces Garak's own artifacts
(``report.jsonl``, ``hitlog.jsonl``, ``report.html``) rather than a bespoke
result format.

Layout::

    garak_pwnzz/
        settings.py         run-time target configuration (loopback-guarded)
        target_facts.py     ground truth read out of the pinned application source
        bootstrap.py        makes ``garak.{generators,probes,detectors}.pwnzz`` importable
        garak_plugins/      the plugin modules themselves
        suites.py           named experiment suites
        runner.py           drives garak in-process, one run directory per suite
        analysis/           reads garak's report.jsonl back into tables and figures

Entry point: ``python -m garak_pwnzz --help``
"""

__version__ = "1.0.0"

__all__ = ["__version__"]
