"""
sphinxnotes.data.render
~~~~~~~~~~~~~~~~~~~~~~~

Module for rendering data to doctree nodes.

:copyright: Copyright 2025 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, final, cast, Callable
from abc import abstractmethod, ABC
from dataclasses import dataclass

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform, ReferencesResolver

from .data import Field, Schema, RawData, ParsedData, PendingData
from .template import Template, Phase, Context
from . import utils

if TYPE_CHECKING:
    from typing import Literal
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.config import Config
    from .template import MarkupParser

logger = logging.getLogger(__name__)

# ========================
# Who is caller of render?
# ========================

# Possible caller of :meth:`pending_node.render` on source parse phase
# (parsing, parsed).
type ParseCaller = SphinxDirective | SphinxRole
# Possible caller of :meth:`pending_node.render` on transform phase.
type TransformCaller = SphinxTransform | SphinxPostTransform
# Possible caller of :meth:`pending_node.render`.
type Caller = ParseCaller | TransformCaller


@dataclass
class _Caller:
    v: Caller

    @property
    def env(self) -> BuildEnvironment:
        return self.v.env

    @property
    def config(self) -> Config:
        return self.v.config

    @property
    def doctree(self) -> nodes.document:
        if isinstance(self.v, SphinxDirective):
            return self.v.state.document
        elif isinstance(self.v, SphinxRole):
            return self.v.inliner.document
        elif isinstance(self.v, SphinxTransform):
            return self.v.document
        else:
            raise NotImplementedError

    @property
    def markup_parser(self) -> MarkupParser:
        if isinstance(self.v, SphinxDirective):
            return self.v.parse_text_to_nodes
        elif isinstance(self.v, SphinxRole):

            def wrapper(text: str) -> list[nodes.Node]:
                return utils.role_parse_text_to_nodes(self.v, text)

            return wrapper
        else:
            return utils.parse_text_to_nodes

    @property
    def parent_node(self) -> nodes.Element | None:
        if isinstance(self.v, SphinxDirective):
            return self.v.state.parent
        elif isinstance(self.v, SphinxRole):
            return self.v.inliner.parent
        else:
            return None

    def reporter(self, e: ValueError) -> Exception:
        if isinstance(self, SphinxDirective):
            raise self.error(str(e))
        elif isinstance(self, SphinxRole):
            ...  # TODO
        else:
            ...  # TODO


# ================
# Nodes definitons
# ================


class RenderedNode(nodes.Element):
    data: ParsedData  # FIXME
    external_name: nodes.Node | None
    external_content: list[nodes.Node]


class rendered_node(RenderedNode, nodes.container): ...


class rendered_inline_node(RenderedNode, nodes.inline): ...


class pending_node(nodes.Element, nodes.Invisible, utils.NotPicklable):
    #: The context.
    ctx: Context
    #: Template for rendering the context.
    template: Template
    #: Extra contexts, as a supplement to the context.
    extra: list[Context]

    inline: bool = False
    need_external_name: bool = False
    need_external_content: bool = False

    # extra ctx: markup(before paring) relation(just after ReferencesResolver)
    # all: env config doctree

    def __init__(
        self, data: Context, tmpl: Template, rawsource='', *children, **attributes
    ):
        super().__init__(rawsource, *children, **attributes)
        self.ctx = data
        self.template = tmpl
        self.extra = []

    def render(self, caller: Caller, replace: bool = False) -> RenderedNode:
        rendered = rendered_inline_node() if self.inline else rendered_node()
        rendered.update_all_atts(self)

        _caller = _Caller(caller)

        if isinstance(self.ctx, PendingData):
            self._resolve_external(self.ctx.raw, _caller)

        rendered += self.template.render(
            _caller.markup_parser, self.ctx, extra=self.extra
        )

        if replace:
            self.replace_self(rendered)

        return rendered

    def _resolve_external(self, data: RawData, caller: _Caller) -> None:
        if not data.name and self.need_external_name:
            if ns := self._resolve_external_name(caller.parent_node):
                data.name = ns.astext()
        if not data.content and self.need_external_content:
            if ns := self._resolve_external_content():
                data.content = '\n\n'.join([x.astext() for x in ns])

    def _resolve_external_name(
        self, caller_parent: nodes.Element | None
    ) -> nodes.Node | None:
        # NOTE: the pending_data_node may be just created and haven't inserted
        # to doctree (on Phase.Parsing).
        return utils.find_titular_node_upward(self.parent or caller_parent)

    def _resolve_external_content(self) -> list[nodes.Node]:
        if not self.parent:
            return []  # TODO
        contnodes = []
        for i, child in enumerate(self.parent):
            if child == self:
                contnodes = self.parent[i:]
                break
        return contnodes


# =============
# Extra context
# =============

type ParseContextGenerator = Callable[[ParseCaller], Context]
type TransformContextGenerator = Callable[[TransformCaller], Context]


class ExtraContextRegistry:
    parsing_gens: list[ParseContextGenerator]
    parsed_gens: list[ParseContextGenerator]
    post_transform_gens: list[TransformContextGenerator]

    def __init__(self) -> None:
        self.parsed_gens = []
        self.parsing_gens = []
        self.post_transform_gens = []

    def add_parse_generator(
        self, phase: Literal[Phase.Parsing, Phase.Parsed], gen: ParseContextGenerator
    ) -> None:
        if phase == Phase.Parsing:
            self.parsing_gens.append(gen)
        else:
            self.parsed_gens.append(gen)

    def add_transform_generator(
        self, phase: Literal[Phase.PostTranform], gen: TransformContextGenerator
    ) -> None:
        self.post_transform_gens.append(gen)

    def _on_parsing(self, caller: ParseCaller) -> list[Context]:
        ctxs = []
        for gen in self.parsing_gens:
            ctxs.append(gen(caller))
        return ctxs

    def _on_parsed(self, caller: ParseCaller) -> list[Context]:
        ctxs = []
        for gen in self.parsed_gens:
            ctxs.append(gen(caller))
        return ctxs

    def _on_post_transform(self, caller: TransformCaller) -> list[Context]:
        ctxs = []
        for gen in self.post_transform_gens:
            ctxs.append(gen(caller))
        return ctxs


EXTRACTX_REGISTRY = ExtraContextRegistry()

# ===============
# Render workflow
# ===============
#
# 1. Define data: BaseDataDefiner generates a pending_node, which contains:
#
#    - Context(Data), Extra contexts
#    - Schema (for verifing Data)
#    - Template
#
# 2. Render data: Some one (Caller) calls pending_node.render during the
#
#    1. On Phase.Parsing: Called by BaseDataDefineDirective and
#       BaseDataDefineRole
#    2. On Phase.Parsed: Called by _ParsedHook.
#    3. On Phase.Resolving: Called by _ResolvingHook.


class BaseDataDefiner(ABC):
    """
    A abstract class that owns :cls:`RawData` and support
    validating and rendering the data at the appropriate time.

    The subclasses *MUST* be subclass of :cls:`SphinxDirective` or
    :cls:`SphinxRole`.
    """

    """Methods to be implemented."""

    @abstractmethod
    def current_raw_data(self) -> RawData: ...

    @abstractmethod
    def current_templates(self) -> list[Template]: ...

    @abstractmethod
    def current_schema(self) -> Schema: ...

    """Methods to be overrided."""

    def process_raw_data(self, data: RawData) -> None: ...

    def process_paresd_data(self, data: ParsedData) -> None: ...

    def process_pending_node(self, n: pending_node) -> None: ...

    def process_rendered_node(self, n: RenderedNode) -> None: ...

    """Methods used internal."""

    @final
    def build_pending_node(self, ctx: Context, tmpl: Template) -> pending_node:
        if isinstance(ctx, PendingData):
            self.process_raw_data(ctx.raw)

        pending = pending_node(ctx, tmpl)
        self.process_pending_node(pending)
        return pending

    @final
    def render_pending_node(self, pending: pending_node) -> RenderedNode:
        caller = cast(Caller, self)
        rendered = pending.render(caller)
        self.process_paresd_data(rendered.data)
        self.process_rendered_node(rendered)

        return rendered

    @final
    def render(self) -> list[nodes.Node]:
        data = self.current_raw_data()
        schema = self.current_schema()
        tmpls = self.current_templates()

        pendings = []
        for tmpl in tmpls:
            ctx = PendingData(data, schema)
            pendings.append(self.build_pending_node(ctx, tmpl))

        ns = []
        for n in pendings:
            if n.template.phase != Phase.Parsing:
                caller = cast(ParseCaller, self)
                n.extra.extend(EXTRACTX_REGISTRY._on_parsing(caller))
                ns.append(n)
            else:
                ns.append(self.render_pending_node(n))

        return ns


class BaseDataDefineDirective(BaseDataDefiner, SphinxDirective):
    @override
    def current_raw_data(self) -> RawData:
        return RawData(
            ' '.join(self.arguments) if self.arguments else None,
            self.options.copy(),
            '\n'.join(self.content) if self.has_content else None,
        )

    @override
    def process_pending_node(self, n: pending_node) -> None:
        self.set_source_info(n)
        n.inline = False

    @override
    def run(self) -> list[nodes.Node]:
        return self.render()


class BaseDataDefineRole(BaseDataDefiner, SphinxRole):
    @override
    def current_raw_data(self) -> RawData:
        return RawData(None, {}, self.text)

    @override
    def process_pending_node(self, n: pending_node) -> None:
        self.set_source_info(n)
        n.inline = True

    @override
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        return self.render(), []


class StrictDataDefineDirective(BaseDataDefineDirective):
    final_argument_whitespace = True

    schema: Schema
    template: Template

    @override
    def current_templates(self) -> list[Template]:
        return [self.template]

    @override
    def current_schema(self) -> Schema:
        return self.schema

    @classmethod
    def derive(
        cls, name: str, schema: Schema, tmpl: Template
    ) -> type[StrictDataDefineDirective]:
        """Generate an AnyDirective child class for describing object."""
        if not schema.name:
            required_arguments = 0
            optional_arguments = 0
        elif schema.name.required:
            required_arguments = 1
            optional_arguments = 0
        else:
            required_arguments = 0
            optional_arguments = 1

        assert not isinstance(schema.attrs, Field)
        option_spec = {}
        for name, field in schema.attrs.items():
            if field.required:
                option_spec[name] = directives.unchanged_required
            else:
                option_spec[name] = directives.unchanged

        has_content = schema.content is not None

        # Generate directive class
        return type(
            '%sStrictDataDefineDirective' % name.title(),
            (cls,),
            {
                'schema': schema,
                'template': tmpl,
                'has_content': has_content,
                'required_arguments': required_arguments,
                'optional_arguments': optional_arguments,
                'option_spec': option_spec,
            },
        )


class _ParsedHook(SphinxDirective):
    def run(self) -> list[nodes.Node]:
        logger.warning(f'running parsed hook for doc {self.env.docname}...')

        # Save origin system_message method.
        orig_sysmsg = self.state_machine.reporter.system_message

        for pending in self.state.document.findall(pending_node):
            if pending.template.phase != Phase.Parsed:
                continue

            # Hook system_message method to let it report the
            # correct line number.
            def fix_lineno(level, message, *children, **kwargs):
                kwargs['line'] = pending.line
                return orig_sysmsg(level, message, *children, **kwargs)

            self.state_machine.reporter.system_message = fix_lineno

            pending.extra.extend(EXTRACTX_REGISTRY._on_parsed(self))
            pending.render(self, replace=True)

        # Restore system_message method.
        self.state_machine.reporter.system_message = orig_sysmsg

        return []  # nothing to return


def _insert_parsed_hook(app, docname, content):
    # NOTE: content is a single element list, representing the content of the
    # source file.
    #
    # .. seealso:: https://www.sphinx-doc.org/en/master/extdev/event_callbacks.html#event-source-read
    #
    # TODO: markdown?
    # TODO: rst_prelog?
    content[-1] = content[-1] + '\n\n.. data.parsed-hook::'


class _ResolvingHook(SphinxTransform):
    # After resolving pending_xref.
    default_priority = (ReferencesResolver.default_priority or 10) + 5

    def apply(self, **kwargs):
        logger.warning(f'running resolving hook for doc {self.env.docname}...')

        for pending in self.document.findall(pending_node):
            if pending.template.phase != Phase.PostTranform:
                # TODO: deal with ValueError
                continue

            pending.extra.extend(EXTRACTX_REGISTRY._on_post_transform(self))
            pending.render(self, replace=True)


def setup(app: Sphinx) -> None:
    # Hook for Phase.Parsed.
    app.add_directive('data.parsed-hook', _ParsedHook)
    app.connect('source-read', _insert_parsed_hook)

    # Hook for Phase.Resolving.
    app.add_transform(_ResolvingHook)
