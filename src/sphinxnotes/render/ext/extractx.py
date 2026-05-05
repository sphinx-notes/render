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
    from sphinx.environment import BuildEnvironment


@extra_context('markup')
class MarkupExtraContext(ExtraContext):
    @override
    def generate(self, request: ExtraContextRequest) -> Any:
        host = request.host
        if not isinstance(host, (SphinxDirective, SphinxRole)):
            raise ValueError(
                f'Extra context "markup" is not available at phase {request.phase}.'
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
    def generate(self, request: ExtraContextRequest) -> Any:
        return proxy(HostWrapper(request.host).doctree)


@extra_context('section')
class SectionExtraContext(ExtraContext):
    @override
    def generate(self, request: ExtraContextRequest) -> Any:
        if request.node.parent is not None:
            parent = request.node.parent
        elif isinstance(request.host, SphinxDirective):
            parent = request.host.state.parent
        elif isinstance(request.host, SphinxRole):
            parent = request.host.inliner.parent
        elif isinstance(request.host, SphinxTransform):
            parent = request.host.document
        else:
            parent = None
        return proxy(find_current_section(parent))


@extra_context('app')
class SphinxAppExtraContext(ExtraContext):
    @override
    def generate(self, request: ExtraContextRequest) -> Any:
        return proxy(request.env.app)


@extra_context('env')
class SphinxBuildEnvExtraContext(ExtraContext):
    @override
    def generate(self, request: ExtraContextRequest) -> Any:
        return proxy(request.env)


def setup(app: Sphinx):
    meta.pre_setup(app)
    return meta.post_setup(app)
