"""Base interface for LLM-as-a-Judge backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseJudge(ABC):
    """Abstract interface implemented by all judge backends."""

    @abstractmethod
    def judge(self, *, system_prompt: str, user_prompt: str) -> str:
        """Send a judging request to an LLM and return its raw text reply."""
        raise NotImplementedError