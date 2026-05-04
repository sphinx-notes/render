"""
This module wraps the :py:mod:`sphinxnotes.render.data` module into context
suitable for use with Jinja templates.
"""

from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
from collections.abc import Hashable
from .data import ParsedData

type ResolvedContext = ParsedData | dict[str, Any]
"""Resolved context types used by template rendering."""


class UnresolvedContext(ABC, Hashable):
    """An abstract representation of context that will be resolved later."""

    @abstractmethod
    def resolve(self) -> ResolvedContext:
        """This method will be called when rendering to get the available
        :py:type:`ResolvedContext`."""
        ...
