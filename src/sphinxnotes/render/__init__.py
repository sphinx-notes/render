"""
sphinxnotes.render
~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from . import meta
from .data import (
    Registry as DataRegistry,
    REGISTRY as DATA_REGISTRY,
    PlainValue,
    Value,
    ValueWrapper,
    RawData,
    ParsedData,
    Field,
    Schema,
)

from .render import (
    Phase,
    Template,
    Host,
)
from .ctx import PendingContext, ResolvedContext
from .ctxnodes import pending_node
from .extractx import ExtraContextRegistry, ExtraContextGenerator
from .pipeline import BaseContextRole, BaseContextDirective
from .sources import (
    UnparsedData,
    BaseDataDefineRole,
    BaseDataDefineDirective,
    StrictDataDefineDirective,
)

if TYPE_CHECKING:
    from sphinx.application import Sphinx


"""Python API for other Sphinx extesions."""
__all__ = [
    'Registry',
    'PlainValue',
    'Value',
    'ValueWrapper',
    'RawData',
    'ParsedData',
    'Field',
    'Schema',
    'Phase',
    'Template',
    'Host',
    'PendingContext',
    'ResolvedContext',
    'pending_node',
    'BaseContextRole',
    'BaseContextDirective',
    'UnparsedData',
    'BaseDataDefineRole',
    'BaseDataDefineDirective',
    'StrictDataDefineDirective',
]


class Registry:
    """The global, all-in-one registry for user."""

    @property
    def data(self) -> DataRegistry:
        return DATA_REGISTRY

    @property
    def extra_context(cls) -> ExtraContextRegistry:
        return ExtraContextGenerator.registry


REGISTRY = Registry()

def setup(app: Sphinx):
    meta.pre_setup(app)

    from . import pipeline, extractx, template

    pipeline.setup(app)
    extractx.setup(app)
    template.setup(app)

    return meta.post_setup(app)
