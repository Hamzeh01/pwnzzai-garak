"""Evidence-linked mitigation matrix.

Each entry ties a concrete finding to the OWASP LLM Top 10 (2025) category it
belongs to, the detector whose hits are the evidence, and the practical controls
that would reduce it. ``analyze.py`` emits this as ``mitigations.csv`` next to
the results so a reader can trace every recommendation back to a measured signal
rather than to opinion.

The assignment weights mitigations and reasoning above raw attack counts, and is
explicit that unedited tool output without analysis is penalised; this registry
is the analysis-to-recommendation bridge.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Mitigation:
    """One finding tied to its OWASP class, evidence detectors, and controls."""
    finding_id: str
    owasp: str
    finding: str
    #: Detector(s) whose hits evidence the finding.
    evidence_detectors: tuple[str, ...]
    #: Where the fix belongs in the stack.
    control_layer: str
    controls: tuple[str, ...]
    #: Why a prompt-only fix is insufficient here.
    residual_risk: str


MITIGATIONS: tuple[Mitigation, ...] = (
    Mitigation(
        finding_id="M-01",
        owasp="LLM01",
        finding="Hardening the system prompt lowers but never eliminates coupon leakage.",
        evidence_detectors=("pwnzz.CouponLeak", "pwnzz.SecretAcknowledged"),
        control_layer="architecture",
        controls=(
            "Do not place the secret in model context; resolve coupons server-side "
            "behind an authorization check the model cannot see.",
            "Enforce a server-side output policy that refuses any response matching "
            "the protected value.",
            "Run an intent classifier ahead of the model so extraction attempts are "
            "handled outside the persona being social-engineered.",
        ),
        residual_risk="Any secret in-context can be surfaced by a phrasing the model will comply with.",
    ),
    Mitigation(
        finding_id="M-02",
        owasp="LLM05",
        finding="Naive output filters (whole-word, substring) miss obfuscated renderings of the secret.",
        evidence_detectors=("pwnzz.CouponLeak", "pwnzz.CouponSuppressed"),
        control_layer="output-handling",
        controls=(
            "Normalise output (strip separators, fold leetspeak, collapse whitespace) "
            "before matching, or keep the secret out of scope entirely.",
            "Prefer allow-listed structured responses over free text where a secret "
            "could appear.",
        ),
        residual_risk="Single-representation filters are defeated by trivial reformatting.",
    ),
    Mitigation(
        finding_id="M-03",
        owasp="LLM01",
        finding="Input filters are bypassed by encoded channels and pure-ASCII foreign language.",
        evidence_detectors=("pwnzz.CouponLeak", "pwnzz.InputRejected"),
        control_layer="input-handling",
        controls=(
            "Treat decoded auxiliary content (base64/ROT13) as untrusted data; never "
            "re-merge it into the instruction context.",
            "Apply the same content policy to decoded and translated text.",
            "Do not treat language restriction as a security control.",
        ),
        residual_risk="Keyword and script gates only stop payloads that had to use the blocked form.",
    ),
    Mitigation(
        finding_id="M-04",
        owasp="LLM01",
        finding="Instructions smuggled through an uploaded QR image are decoded and obeyed.",
        evidence_detectors=("pwnzz.CouponLeak", "pwnzz.ToolExecutionInduced"),
        control_layer="input-handling",
        controls=(
            "Quote content extracted from uploads (QR/OCR/file bodies) to the model as "
            "data, never as instructions.",
            "Apply the same input policy to extracted content as to typed input.",
        ),
        residual_risk="Any data channel the app decodes becomes an instruction channel by default.",
    ),
    Mitigation(
        finding_id="M-05",
        owasp="LLM02",
        finding="The RAG assistant is configured to disclose customer PII on request.",
        evidence_detectors=("pwnzz.CustomerPII", "pwnzz.SystemPromptLeak"),
        control_layer="data-governance",
        controls=(
            "Redact PII at index time so it is never retrievable.",
            "Remove instructions that permit disclosure from the system prompt.",
            "Add an output DLP check for PII shapes before responses leave the app.",
        ),
        residual_risk="If PII is retrievable, prompt-level rules will eventually be talked around.",
    ),
    Mitigation(
        finding_id="M-06",
        owasp="LLM06",
        finding="The agentic SQL tool and order assistant can read across tenants.",
        evidence_detectors=("pwnzz.CrossTenantFlag", "pwnzz.DatabaseErrorLeak"),
        control_layer="authorization",
        controls=(
            "Scope every tool/query to the authenticated principal server-side; the "
            "model must not choose whose rows to read.",
            "Parameterise SQL and constrain the agent to a least-privilege view.",
            "Never surface raw database errors to the user.",
        ),
        residual_risk="Model-chosen queries with app-level DB rights are horizontal privilege escalation waiting to happen.",
    ),
    Mitigation(
        finding_id="M-07",
        owasp="LLM04",
        finding="A few mislabelled comments create a targeted sentiment backdoor.",
        evidence_detectors=("pwnzz.SentimentLabelFlip",),
        control_layer="data-governance",
        controls=(
            "Treat feedback/training data as an attack surface: provenance, review, "
            "and label-distribution anomaly detection before any retrain.",
            "Keep an unpoisoned holdout and monitor drift on trigger terms.",
        ),
        residual_risk="Bag-of-words models are cheap to backdoor with a distinctive trigger phrase.",
    ),
    Mitigation(
        finding_id="M-08",
        owasp="LLM04",
        finding="Trusted-only retrieval reduces but does not eliminate RAG poisoning influence.",
        evidence_detectors=("pwnzz.PoisonedRetrievalInfluence",),
        control_layer="retrieval",
        controls=(
            "Combine trust-tagged retrieval with output grounding checks.",
            "Do not let a single untrusted passage dictate a policy claim.",
            "Require corroboration across trusted sources for mandatory-sounding rules.",
        ),
        residual_risk="Retrieval-time trust filtering is necessary but not sufficient on its own.",
    ),
)


def as_rows() -> list[list[str]]:
    """Return the mitigation matrix as header + string rows for CSV export."""
    header = [
        "finding_id", "owasp", "finding", "evidence_detectors",
        "control_layer", "controls", "residual_risk",
    ]
    rows = [header]
    for m in MITIGATIONS:
        rows.append([
            m.finding_id,
            m.owasp,
            m.finding,
            "; ".join(m.evidence_detectors),
            m.control_layer,
            " | ".join(m.controls),
            m.residual_risk,
        ])
    return rows
