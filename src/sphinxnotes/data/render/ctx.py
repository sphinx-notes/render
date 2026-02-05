"""
sphinxnotes.data.render.data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This module wraps the :mod:`..data` module to make it work well with the render
pipeline (:mod:`pipeline`).
"""

from typing import TYPE_CHECKING, override
from abc import ABC, abstractmethod
from collections.abc import Hashable
from dataclasses import dataclass

from sphinxnotes.data.utils import Unpicklable

from ..data import ParsedData, RawData, Schema

if TYPE_CHECKING:
    from typing import Any

type Context = PendingContextRef | ResolvedContext

type ResolvedContext = ParsedData | dict[str, Any]


@dataclass
class PendingContextRef:
    """A abstract class that references to :cls:`PendingCtx`."""

    ref: int
    chksum: int

    def __hash__(self) -> int:
        return hash((self.ref, self.chksum))


class PendingContext(ABC, Unpicklable, Hashable):
    """A abstract represent of context that is not currently available.

    Call :meth:`resolve` to get data.
    """

    @abstractmethod
    def resolve(self) -> ResolvedContext: ...


class PendingContextStorage:
    """Area for temporarily storing PendingData.

    This class is indented to resolve the problem that some datas are Unpicklable
    and can not be hold by :cls:`pending_node` (as ``pending_node`` will be
    pickled along with the docutils doctree)

    This class maintains a mapping from :cls:`PendingDataRef` -> :cls:`PendingData`.
    ``pending_node`` owns the ``PendingDataRef``, and the PendingData is Unpicklable,
    pending_node can get it by calling :meth:`retrieve`.
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


PENDING_CONTEXT_STORAGE = PendingContextStorage()


@dataclass
class UnparsedData(PendingContext):
    """A implementation of PendingData, contains raw data and its schema."""

    raw: RawData
    schema: Schema

    @override
    def resolve(self) -> ResolvedContext:
        return self.schema.parse(self.raw)

    @override
    def __hash__(self) -> int:
        return hash((self.raw, self.schema))
