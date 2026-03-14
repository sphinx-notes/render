"""
This module wraps the :py:mod:`sphinxnote.render.data` module into context
suitable for use with Jinja templates.
"""

from typing import Any
from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass

from .data import ParsedData
from .utils import Unpicklable

type ResolvedContext = ParsedData | dict[str, Any]
"""The context is """


@dataclass
class PendingContextRef:
    """A abstract class that references to :class:`PendingCtx`."""

    ref: int
    chksum: int

    def __hash__(self) -> int:
        return hash((self.ref, self.chksum))


class PendingContext(ABC, Unpicklable, Hashable):
    """A abstract representation of context that is not currently available."""

    @abstractmethod
    def resolve(self) -> ResolvedContext:
        """This method will be called when rendering to get the available
        :py:type:`ResolvedContext`."""
        ...


class PendingContextStorage:
    """Area for temporarily storing :py:class:`PendingContext`.

    This class is indented to resolve the problem that:

        Some of the PendingContext are :class:Unpicklable` and they can not be hold
        by :class:`pending_node` (as ``pending_node`` will be pickled along with
        the docutils doctree)

    This class maintains a mapping from :class:`PendingContextRef` -> :cls:`PendingContext`.
    ``pending_node`` owns the ``PendingContextRef``, and can retrieve the context
    by calling :py:meth:`retrieve`.
    """

    _next_id: int
    _data: dict[PendingContextRef, PendingContext] = {}

    def __init__(self) -> None:
        self._next_id = 0
        self._data = {}

    def stash(self, pending: PendingContext) -> PendingContextRef:
        ref = PendingContextRef(self._next_id, hash(pending))
        self._next_id += 1
        self._data[ref] = pending
        return ref

    def retrieve(self, ref: PendingContextRef) -> PendingContext | None:
        data = self._data.pop(ref, None)
        return data
