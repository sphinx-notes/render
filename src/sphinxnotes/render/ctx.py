"""
This module wraps the :py:mod:`sphinxnotes.render.data` module into context
suitable for use with Jinja templates.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from abc import ABC, abstractmethod
from collections.abc import Hashable
from .data import ParsedData

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

type ResolvedContext = ParsedData | dict[str, Any]
"""Resolved context types used by template rendering."""


class UnresolvedContext(ABC, Hashable):
    """An abstract representation of context that will be resolved later."""

    @abstractmethod
    def resolve(self, env: BuildEnvironment) -> ResolvedContext:
        """This method will be called when rendering to get the available
        :py:type:`ResolvedContext`."""
        ...
