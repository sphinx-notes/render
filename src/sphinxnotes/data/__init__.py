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
    pending_node,
    rendered_node,
    BaseDataDefineRole,
    BaseDataDefineDirective,
    ExtraContextRegistry,
    ExtraContextGenerator,
)
from .examples.strict import StrictDataDefineDirective
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
    'ParsedData',
    'Field',
    'Schema',
    'Phase',
    'Template',
    'Host',
    'pending_node',
    'rendered_node',
    'rendered_node',
    'BaseDataDefineRole',
    'BaseDataDefineDirective',
    'StrictDataDefineDirective',
]

logger = logging.getLogger(__name__)


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

    from . import config, render
    from .examples import datadomain

    config.setup(app)
    render.setup(app)
    datadomain.setup(app)

    return meta.post_setup(app)
