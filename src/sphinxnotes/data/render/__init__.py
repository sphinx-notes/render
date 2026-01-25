from __future__ import annotations
from typing import TYPE_CHECKING

from .render import Phase, Template, Host
from .datanodes import pending_node
from .pipeline import (
    BaseDataDefineRole,
    BaseDataDefineDirective,
)
from .extractx import ExtraContextRegistry, ExtraContextGenerator

if TYPE_CHECKING:
    from sphinx.application import Sphinx

"""Python API for render module."""
__all__ = [
    'Phase',
    'Template',
    'Host',
    'pending_node',
    'BaseDataDefineRole',
    'BaseDataDefineDirective',
    'ExtraContextRegistry',
    'ExtraContextGenerator',
]


def setup(app: Sphinx) -> None:
    from . import pipeline, extractx, template

    pipeline.setup(app)
    extractx.setup(app)
    template.setup(app)
