"""
sphinxnotes.render.ctx
~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This module wraps the :mod:`data` into context for rendering the template.
"""

from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass

from .utils import Unpicklable

if TYPE_CHECKING:
    from typing import Any
    from .data import ParsedData

type ResolvedContext = ParsedData | dict[str, Any]


@dataclass
class PendingContextRef:
    """A abstract class that references to :class:`PendingCtx`."""

    ref: int
    chksum: int

    def __hash__(self) -> int:
        return hash((self.ref, self.chksum))


class PendingContext(ABC, Unpicklable, Hashable):
    """A abstract representation of context that is not currently available.

    Call :meth:`resolve` at the right time (depends on the implment) to get
    context available.
    """

    @abstractmethod
    def resolve(self) -> ResolvedContext: ...


class PendingContextStorage:
    """Area for temporarily storing PendingContext.

    This class is indented to resolve the problem that:

        Some of the PendingContext are :class:Unpicklable` and they can not be hold
        by :class:`pending_node` (as ``pending_node`` will be pickled along with
        the docutils doctree)

    This class maintains a mapping from :class:`PendingContextRef` -> :cls:`PendingContext`.
    ``pending_node`` owns the ``PendingContextRef``, and can retrieve the context
    by calling :meth:`retrieve`.
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
