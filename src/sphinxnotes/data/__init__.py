"""
sphinxnotes.data
~~~~~~~~~~~~~~~~

:copyright: Copyright 2025 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from sphinx.util import logging

from . import meta
from .data import (
    Registry,
    PlainValue,
    Value,
    ValueWrapper,
    RawData,
    Data,
    Field,
    Schema,
)
from .template import Phase, Template
from .render import (
    Caller,
    pending_node,
    RenderedNode,
    rendered_node,
    rendered_inline_node,
    BaseDataDefiner,
    BaseDataDefineRole,
    BaseDataDefineDirective,
    StrictDataDefineDirective,
)
from .config import Config

if TYPE_CHECKING:
    from sphinx.application import Sphinx


"""Python API for other Sphinx extesions."""
__all__ = [
    'Config',
    'Registry',
    'PlainValue',
    'Value',
    'ValueWrapper',
    'RawData',
    'Data',
    'Field',
    'Schema',
    'Phase',
    'Template',
    'Caller',
    'pending_node',
    'RenderedNode',
    'rendered_node',
    'rendered_inline_node',
    'BaseDataDefiner',
    'BaseDataDefineRole',
    'BaseDataDefineDirective',
    'BaseDataDefineDirective',
    'StrictDataDefineDirective',
]

logger = logging.getLogger(__name__)


def setup(app: Sphinx):
    meta.pre_setup(app)

    from . import config, template, render, adhoc

    config.setup(app)
    template.setup(app)
    render.setup(app)
    adhoc.setup(app)

    return meta.post_setup(app)
