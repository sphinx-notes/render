"""
sphinxnotes.render.ext.extractx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

Provides useful extra context.

"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, Any

from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform

from .. import meta, extra_context, ExtraContext
from ..extractx import ExtraContextRequest
from ..template import HostWrapper

# FIXME:
from ..utils import find_current_section
from ..utils.ctxproxy import proxy

if TYPE_CHECKING:
    from sphinx.application import Sphinx


@extra_context('markup')
class MarkupExtraContext(ExtraContext):
    @override
    def generate(self, req: ExtraContextRequest) -> Any:
        host = req.host
        if not isinstance(host, (SphinxDirective, SphinxRole)):
            raise ValueError(
                f'Extra context "markup" is not available at phase {req.phase}.'
            )
        isdir = isinstance(host, SphinxDirective)
        return {
            'type': 'directive' if isdir else 'role',
            'name': host.name,
            'lineno': host.lineno,
            'rawtext': host.block_text if isdir else host.rawtext,
        }


@extra_context('doc')
class DocExtraContext(ExtraContext):
    @override
    def generate(self, req: ExtraContextRequest) -> Any:
        return proxy(HostWrapper(req.host).doctree)


@extra_context('section')
class SectionExtraContext(ExtraContext):
    @override
    def generate(self, req: ExtraContextRequest) -> Any:
        if req.node.parent is not None:
            parent = req.node.parent
        elif isinstance(req.host, SphinxDirective):
            parent = req.host.state.parent
        elif isinstance(req.host, SphinxRole):
            parent = req.host.inliner.parent
        elif isinstance(req.host, SphinxTransform):
            parent = req.host.document
        else:
            parent = None
        return proxy(find_current_section(parent))


@extra_context('app')
class SphinxAppExtraContext(ExtraContext):
    @override
    def generate(self, req: ExtraContextRequest) -> Any:
        return proxy(req.env.app)


@extra_context('env')
class SphinxBuildEnvExtraContext(ExtraContext):
    @override
    def generate(self, req: ExtraContextRequest) -> Any:
        return proxy(req.env)


def setup(app: Sphinx):
    meta.pre_setup(app)
    return meta.post_setup(app)
