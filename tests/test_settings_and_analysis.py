"""Loopback guard and report-parsing tests."""

# Test names carry the intent; a docstring restating the name adds nothing.
# pylint: disable=missing-function-docstring

from __future__ import annotations

import json

import pytest

from garak_pwnzz import settings
from garak_pwnzz.analysis import report_reader


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:18080",
        "http://localhost:8080",
        "http://127.0.0.1:18080/",
    ],
)
def test_loopback_urls_allowed(url):
    assert settings.require_loopback(url).startswith("http://")


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:8080",  # public host
        "https://127.0.0.1:18080",  # not plain http
        "http://10.0.0.5:8080",  # private but not loopback
        "http://user:pw@127.0.0.1",  # credentials in url
        "http://127.0.0.1:18080?x=1",  # query string
    ],
)
def test_non_loopback_urls_rejected(url):
    with pytest.raises(ValueError):
        settings.require_loopback(url)


def test_read_attempts_expands_generations(tmp_path):
    # A single attempt with 2 generations must yield 2 records with aligned scores.
    attempt = {
        "entry_type": "attempt",
        "status": 2,
        "probe_classname": "pwnzz.Test",
        "goal": "g",
        "seq": 0,
        "conversations": [
            {
                "turns": [
                    {"role": "user", "content": {"text": "q"}},
                    {
                        "role": "assistant",
                        "content": {"text": "leak A", "notes": {"secret": "x"}},
                    },
                ]
            },
            {
                "turns": [
                    {"role": "user", "content": {"text": "q"}},
                    {
                        "role": "assistant",
                        "content": {"text": "clean B", "notes": {"secret": "x"}},
                    },
                ]
            },
        ],
        "outputs": [{"text": "leak A"}, {"text": "clean B"}],
        "detector_results": {"pwnzz.CouponLeak": [1.0, 0.0]},
    }
    path = tmp_path / "r.report.jsonl"
    path.write_text(json.dumps(attempt) + "\n", encoding="utf-8")

    records = report_reader.read_attempts(path)
    assert len(records) == 2
    assert records[0].generation == 0 and records[0].score("pwnzz.CouponLeak") == 1.0
    assert records[1].generation == 1 and records[1].score("pwnzz.CouponLeak") == 0.0


def test_eval_record_attack_success_rate():
    ev = report_reader.EvalRecord(
        report="r", probe="p", detector="d", passed=6, fails=4, nones=2, total=12
    )
    assert ev.evaluated == 10
    assert ev.attack_success_rate == pytest.approx(0.4)


def test_eval_record_all_none_is_undefined():
    ev = report_reader.EvalRecord(
        report="r", probe="p", detector="d", passed=0, fails=0, nones=5, total=5
    )
    assert ev.attack_success_rate is None
