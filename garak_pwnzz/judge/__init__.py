"""LLM-as-a-judge: a second opinion on whether an attack actually succeeded.

The ground-truth detectors in :mod:`garak.detectors.pwnzz` answer a narrow,
checkable question -- "is the level's exact coupon word present in this
response, in any rendering?" -- and they are right by construction. What they
cannot see is a response that *satisfies the attacker's goal without matching
the pattern*: a paraphrase, a hint that gives the secret away, a refusal that
leaks the answer while declining to state it. That gap is exactly what garak's
own paper says signature detection cannot close.

This package adds a judge model as a supplementary signal for that gap. It is
deliberately *not* promoted to a primary detector. A judge is itself a
language model: it can be prompt-injected by the very evidence it is reading,
it disagrees with itself across runs, and here it is small. Its value is in the
*disagreement* with the ground-truth detectors -- the attempts where the two
signals diverge are the ones worth reading by hand -- not in its raw counts.

Two consumers share this core:

* :mod:`garak.detectors.pwnzz_judge` -- an in-band garak detector, opt-in per
  run via ``PWNZZ_JUDGE=1``, whose scores land in ``report.jsonl`` alongside
  everything else.
* :mod:`garak_pwnzz.analysis.judge_pass` -- a post-hoc pass over
  ``garak_analysis/attempts.csv``, so an existing run can be judged without
  driving another round of attack traffic at the lab.

**Choice of judge model.** The default is whatever ``PWNZZ_OLLAMA_MODEL`` is
set to -- the model the lab already pulled, so enabling the judge installs
nothing. That default makes the judge share weights with the model under
assessment, which is a known bias: a model is a soft grader of its own output
family. Set ``PWNZZ_JUDGE_MODEL`` to an independent model where the
independence matters more than the convenience.
"""

from garak_pwnzz.judge.base import BaseJudge, JudgeUnavailable
from garak_pwnzz.judge.client import OllamaJudge
from garak_pwnzz.judge.criteria import Criteria, get_criteria
from garak_pwnzz.judge.prompts import (
    JUDGE_SYSTEM_PROMPT,
    build_context_block,
    build_user_prompt,
)
from garak_pwnzz.judge.verdict import (
    AMBIGUOUS,
    FAILURE,
    SUCCESS,
    JudgeVerdict,
    parse_judge_response,
)

__all__ = [
    "AMBIGUOUS",
    "FAILURE",
    "SUCCESS",
    "BaseJudge",
    "Criteria",
    "JudgeUnavailable",
    "JudgeVerdict",
    "JUDGE_SYSTEM_PROMPT",
    "OllamaJudge",
    "build_context_block",
    "build_user_prompt",
    "get_criteria",
    "parse_judge_response",
]
