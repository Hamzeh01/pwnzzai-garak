from __future__ import annotations

import json

from src.analysis import sha256_file
from src.probes.phase06_full import (
    AUTHORIZATION_PATH,
    DIRECT_CASE_IDS,
    FINAL_CATALOG_PATH,
    FINAL_PROTOCOL_PATH,
    POISON_CASE_IDS,
    QR_CASE_IDS,
    RAG_CASE_IDS,
    Phase06FullRun,
)
from scripts.validate_phase06_execution import validate_phase06_execution


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_phase06_authorization_is_separate_from_immutable_protocol() -> None:
    protocol = _load(FINAL_PROTOCOL_PATH)
    authorization = _load(AUTHORIZATION_PATH)

    assert protocol["safety"]["allow_full_execution"] is False
    assert protocol["safety"]["authorization_scope"] == "none"
    assert authorization["authorized"] is True
    assert authorization["authorization_scope"] == "phase6_full_only"
    assert authorization["protocol_sha256"] == sha256_file(FINAL_PROTOCOL_PATH)
    assert authorization["catalog_sha256"] == sha256_file(FINAL_CATALOG_PATH)


def test_phase06_matrix_accounts_for_43_records_and_79_requests() -> None:
    catalog = _load(FINAL_CATALOG_PATH)
    cases = {case["test_case_id"]: case for case in catalog["cases"]}
    prompt_case_ids = DIRECT_CASE_IDS | QR_CASE_IDS | RAG_CASE_IDS
    prompt_records = sum(cases[case_id]["repetitions"] for case_id in prompt_case_ids)
    terminal_records = 1 + prompt_records + 1 + 2 * len(POISON_CASE_IDS)
    target_requests = prompt_records + 1 + 5 + 10 * len(POISON_CASE_IDS)

    assert prompt_records == 33
    assert terminal_records == 43
    assert target_requests == 79


def test_phase06_entry_conditions_accept_exact_frozen_scope() -> None:
    protocol = _load(FINAL_PROTOCOL_PATH)
    configured = protocol["principal_target"]
    runner = Phase06FullRun.__new__(Phase06FullRun)
    runner.protocol = protocol
    runner.catalog = _load(FINAL_CATALOG_PATH)
    runner.authorization = _load(AUTHORIZATION_PATH)
    runner.preflight = {
        "status": "passed",
        "protocol_version": "1.1.1",
        "protocol_sha256": sha256_file(FINAL_PROTOCOL_PATH),
        "catalog_sha256": sha256_file(FINAL_CATALOG_PATH),
        "pwnzzai_commit": configured["pwnzzai_commit"],
        "pwnzzai_image_digest": (
            "sha256:7878fbd790a0cc6f698950722b79760aabbb945dcb59a4996bfa2a3937f4849a"
        ),
        "model": configured["model"],
        "model_digest": configured["model_digest"],
        "pwnzzai_listener": "127.0.0.1:18080",
        "ollama_listener": "127.0.0.1:11434",
        "home_status_code": 200,
        "ollama_available": True,
    }

    runner._validate_entry_conditions()


def test_phase06_retained_evidence_is_complete() -> None:
    assert validate_phase06_execution() == []
