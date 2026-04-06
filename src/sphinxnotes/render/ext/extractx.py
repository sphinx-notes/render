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

from .. import meta, extra_context, GlobalExtraContext, ParsingPhaseExtraContext

# FIXME:
from ..utils import find_current_section
from ..utils.ctxproxy import proxy

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


@extra_context('markup')
class MarkupExtraContext(ParsingPhaseExtraContext):
    @override
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any:
        isdir = isinstance(directive, SphinxDirective)
        return {
            'type': 'directive' if isdir else 'role',
            'name': directive.name,
            'lineno': directive.lineno,
            'rawtext': directive.block_text if isdir else directive.rawtext,
        }


@extra_context('doc')
class DocExtraContext(ParsingPhaseExtraContext):
    @override
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any:
        doctree = (
            directive.state.document
            if isinstance(directive, SphinxDirective)
            else directive.inliner.document
        )
        return proxy(doctree)


@extra_context('section')
class SectionExtraContext(ParsingPhaseExtraContext):
    @override
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any:
        parent = (
            directive.state.parent
            if isinstance(directive, SphinxDirective)
            else directive.inliner.parent
        )
        return proxy(find_current_section(parent))


@extra_context('app')
class SphinxAppExtraContext(GlobalExtraContext):
    @override
    def generate(self, env: BuildEnvironment) -> Any:
        return proxy(env.app)


@extra_context('env')
class SphinxBuildEnvExtraContext(GlobalExtraContext):
    @override
    def generate(self, env: BuildEnvironment) -> Any:
        return proxy(env)


def setup(app: Sphinx):
    meta.pre_setup(app)
    return meta.post_setup(app)
