from __future__ import annotations
from typing import TYPE_CHECKING

from .render import (
    Phase,
    Template,
    Host,
)
from .ctx import Context, PendingContext, PendingContextRef, PendingContextStorage, ResolvedContext
from .ctxnodes import pending_node
from .pipeline import (
    BaseContextRole,
    BaseContextDirective,
)
from .extractx import ExtraContextRegistry, ExtraContextGenerator
from .sources import (
    BaseDataDefineDirective,
    StrictDataDefineDirective,
    BaseDataDefineRole,
)

if TYPE_CHECKING:
    from sphinx.application import Sphinx

"""Python API for render module."""
__all__ = [
    'Phase',
    'Template',
    'Host',
    'Context',
    'PendingContext',
    'PendingContextRef',
    'PendingContextStorage',
    'ResolvedContext',
    'pending_node',
    'BaseContextRole',
    'BaseContextDirective',
    'ExtraContextRegistry',
    'ExtraContextGenerator',
    'BaseDataDefineDirective',
    'StrictDataDefineDirective',
    'BaseDataDefineRole',
]


def setup(app: Sphinx) -> None:
    from . import pipeline, extractx, template

    pipeline.setup(app)
    extractx.setup(app)
    template.setup(app)
