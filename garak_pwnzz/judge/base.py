"""The judge backend interface and its one error type."""

from __future__ import annotations

from abc import ABC, abstractmethod


class JudgeUnavailable(RuntimeError):
    """The judge could not be reached or did not answer in time.

    Raised instead of returning a verdict so that callers can record "not
    judged" rather than silently booking a transport failure as "the attack
    did not succeed". Every caller in this project turns it into ``None``.
    """


class BaseJudge(ABC):
    """Abstract interface implemented by all judge backends.

    Backends return the model's raw text. Parsing lives in
    :mod:`garak_pwnzz.judge.verdict` so that a swapped backend cannot quietly
    change how a verdict is interpreted.
    """

    #: Identifies the model behind this backend, recorded with every verdict so
    #: a result can be traced to the judge that produced it.
    model: str

    def check_ready(self) -> None:
        """Raise :class:`JudgeUnavailable` unless this backend can judge now.

        Callers use this to fail fast at the start of a long pass rather than
        after emitting a table of "judge unavailable" rows. The default does
        nothing: a backend with no meaningful precondition is always ready.
        """

    @abstractmethod
    def judge(self, *, system_prompt: str, user_prompt: str) -> str:
        """Send a judging request to an LLM and return its raw text reply.

        Raises:
            JudgeUnavailable: if the backend could not be reached, timed out,
                or returned a transport-level error.
        """
        raise NotImplementedError
