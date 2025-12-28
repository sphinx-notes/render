"""
sphinxnotes.dataview
~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives

from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.application import Sphinx
from sphinx.transforms import SphinxTransform

from . import meta
from .freestyle import FreeStyleDirective, FreeStyleOptionSpec
from .data import Data, Field, Schema, Raw
from .render import Template, Phase, render, JinjaEnv
from .utils import find_current_document, find_current_section, TempData
from .context_proxy import proxy

logger = logging.getLogger(__name__)


class Node(nodes.Element): ...


class pending_node(Node, nodes.meta): ...


class rendered_node(Node, nodes.container): ...


class TemplateStore(TempData[Template]): ...


class RawDataStore(TempData[Raw]): ...


class SchemaStore(TempData[Schema]): ...


class TemplateDirective(SphinxDirective):
    option_spec = {
        'on': Phase.option_spec,
        'debug': directives.flag,
    }
    has_content = True

    def run(self) -> list[nodes.Node]:
        self.assert_has_content()

        tmpl = Template(
            text='\n'.join(self.content),
            phase=self.options.get('on', Phase.default()),
            debug='debug' in self.options,
        )
        TemplateStore.set(self.state.document, tmpl)

        return []


class DataSchemaDirective(FreeStyleDirective):
    optional_arguments = 1
    option_spec = FreeStyleOptionSpec()
    has_content = True

    def run(self) -> list[nodes.Node]:
        if self.arguments:
            name = Field.from_str(self.arguments[0])
        else:
            name = None

        attrs = {}
        for k, v in self.options.items():
            attrs[k] = Field.from_str(v)

        if self.content:
            content = Field.from_str(self.content[0])
        else:
            content = None

        schema = Schema(name, attrs, content)
        SchemaStore.set(self.state.document, schema)

        return []


def markup_context(v: SphinxDirective | SphinxRole | nodes.Element) -> dict[str, Any]:
    ctx = {}

    if isinstance(v, nodes.Element):
        ctx['_markup'] = {}
    else:
        isdir = isinstance(v, SphinxDirective)
        ctx['_markup'] = {
            'type': 'directive' if isdir else 'role',
            'name': v.name,
            'lineno': v.lineno,
            'rawtext': v.block_text if isdir else v.rawtext,
        }
    return ctx


def doctree_context(v: SphinxDirective | SphinxRole | nodes.Element) -> dict[str, Any]:
    ctx = {}
    if isinstance(v, nodes.Element):
        ctx['_doc'] = proxy(find_current_document(v))
        ctx['_section'] = proxy(find_current_section(v))
    else:
        isdir = isinstance(v, SphinxDirective)
        state = v.state if isdir else v.inliner
        ctx['_doc'] = proxy(state.document)
        ctx['_section'] = proxy(find_current_section(state.parent))
    return ctx


def sphinx_context(v: SphinxDirective | SphinxRole | SphinxTransform) -> dict[str, Any]:
    ctx = {}
    ctx['_env'] = proxy(v.env)
    ctx['_config'] = proxy(v.config)
    return ctx


class DataDefineDirective(FreeStyleDirective):
    optional_arguments = 1
    has_content = True

    def run(self) -> list[nodes.Node]:
        tmpl = TemplateStore.get(self.state.document)
        if tmpl is None:
            return []

        schema = SchemaStore.get(self.state.document)
        rawdata = self._raw_data()

        if tmpl.phase != Phase.Parsing:
            n = pending_node()
            RawDataStore.set(n, rawdata)
            TemplateStore.set(n, tmpl)
            if schema:
                SchemaStore.set(n, schema)
            return [n]

        if schema:
            try:
                data = schema.parse(rawdata)
            except ValueError as e:
                raise self.error(str(e))
        else:
            data = Data.from_raw(rawdata)

        extra_ctx = {
            **sphinx_context(self),
            **doctree_context(self),
            **markup_context(self),
        }
        n = render(self.parse_text_to_nodes, tmpl, data, extra_ctx)

        return [n]

    def _raw_data(self) -> Raw:
        return Raw(
            self.arguments[0] if self.arguments else None,
            self.options.copy(),
            '\n'.join(self.content),
        )


class ParsedHookDirective(SphinxDirective):
    def run(self) -> list[nodes.Node]:
        for pending in self.state.document.findall(pending_node):
            tmpl = TemplateStore.get(pending)
            schema = SchemaStore.get(pending)
            rawdata = RawDataStore.get(pending)

            assert tmpl
            assert rawdata

            if schema:
                try:
                    data = schema.parse(rawdata)
                except ValueError as e:
                    raise self.error(str(e))
            else:
                data = Data.from_raw(rawdata)

            extra_ctx = {
                **sphinx_context(self),
                **doctree_context(pending),
                **markup_context(pending),
            }
            n = render(self.parse_text_to_nodes, tmpl, data, extra_ctx)
            pending.replace_self(n)

        return []  # nothing to return


def on_source_read(app, docname, content):
    # NOTE: content is a single element list, representing the content of the
    # source file.
    #
    # .. seealso:: https://www.sphinx-doc.org/en/master/extdev/event_callbacks.html#event-source-read
    content[-1] = content[-1] + '\n\n.. data:parsed-hook::'


class ResolvingHookTransform(SphinxTransform):
    default_priority = 210  # 在主要处理阶段运行

    def apply(self, **kwargs):
        for pending in self.document.findall(pending_node):
            tmpl = TemplateStore.get(pending)
            schema = SchemaStore.get(pending)
            rawdata = RawDataStore.get(pending)

            assert tmpl
            assert rawdata

            if schema:
                try:
                    data = schema.parse(rawdata)
                except ValueError:
                    continue  # FIXME
            else:
                data = Data.from_raw(rawdata)

            n = render(self.parse_text_to_nodes, tmpl, data, {})
            pending.replace_self(n)


def setup(app: Sphinx):
    meta.pre_setup(app)

    app.add_directive('data:tmpl', TemplateDirective, False)
    app.add_directive('data:schema', DataSchemaDirective, False)
    # app.add_directive('data:use-tmpl', DataTemplateDirective, False)
    app.add_directive('data:def', DataDefineDirective, False)
    app.add_directive('data:parsed-hook', ParsedHookDirective, False)

    app.connect('source-read', on_source_read)

    app.add_transform(ResolvingHookTransform)

    JinjaEnv.setup(app)

    return meta.post_setup(app)
