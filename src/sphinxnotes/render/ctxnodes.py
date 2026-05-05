from __future__ import annotations
from typing import TYPE_CHECKING, override
import pickle
from pprint import pformat

from docutils import nodes
from docutils.parsers.rst.states import Inliner

from .data import ValueWrapper, ParsedData
from .template import Template, Phase
from .ctx import (
    UnresolvedContext,
    ResolvedContext,
)
from .extractx import ExtraContextGenerator
from .markup import MarkupRenderer
from .jinja import TemplateRenderer
from .utils import (
    Report,
    Reporter,
    find_nearest_block_element,
)

if TYPE_CHECKING:
    from typing import Callable
    from .markup import Host
    from .ctx import ResolvedContext


class pending_node(nodes.Element):
    """A docutils node to be rendered."""

    # The context to be rendered by Jinja template.
    ctx: UnresolvedContext | ResolvedContext
    #: Jinja template for rendering the context.
    template: Template
    #: Whether rendering to inline nodes.
    inline: bool
    #: Whether the rendering pipeline is finished (failed is also finished).
    rendered: bool
    #: Stored pickling error for later-phase unresolved context.
    _ctx_pickle_error: Exception | None

    def __init__(
        self,
        ctx: UnresolvedContext | ResolvedContext,
        tmpl: Template,
        inline: bool = False,
        rawsource='',
        *children,
        **attributes,
    ) -> None:
        super().__init__(rawsource, *children, **attributes)
        self._ctx_pickle_error = None
        if isinstance(ctx, UnresolvedContext) and tmpl.phase != Phase.Parsing:
            try:
                pickle.dumps(ctx)
            except Exception as exc:
                self._ctx_pickle_error = exc
        self.ctx = ctx
        self.template = tmpl
        self.inline = inline
        self.rendered = False

        # Init hook lists.
        self._unresolved_context_hooks = []
        self._resolved_data_hooks = []
        self._markup_text_hooks = []
        self._rendered_nodes_hooks = []

    def render(self, host: Host) -> None:
        """
        The core function for rendering context and template to docutils nodes.

        1. UnresolvedContext -> ResolvedContext
        2. TemplateRenderer.render(ResolvedContext) -> Markup Text (``str``)
        3. MarkupRenderer.render(Markup Text) -> doctree Nodes (list[nodes.Node])
        """

        # Make sure the function is called once.
        assert not self.rendered
        self.rendered = True

        # Clear previous empty reports.
        Reporter(self).clear_empty()
        # Create debug report.
        report = Report('Render Report', 'DEBUG', source=self.source, line=self.line)

        # Constructor for error report.
        def err_report() -> Report:
            if self.template.debug:
                # Reuse the render report as possible.
                report['type'] = 'ERROR'
                return report
            return Report('Render Report', 'ERROR', source=self.source, line=self.line)

        if self._ctx_pickle_error is not None:
            report = err_report()
            report.text(
                f'UnresolvedContext used by {self.template.phase} phase templates '
                'must be picklable:'
            )
            report.exception(self._ctx_pickle_error)
            self += report
            return None

        # 1. Prepare context for Jinja template.
        if isinstance(self.ctx, UnresolvedContext):
            pdata = self.ctx
            report.text('Unresolved context:')
            report.code(pformat(pdata), lang='python')

            for hook in self._unresolved_context_hooks:
                hook(self, pdata)

            try:
                ctx = self.ctx = pdata.resolve()
            except Exception as e:
                report = err_report()
                report.text('Failed to resolve unresolved context:')
                report.exception(e)
                self += report
                return None
        else:
            ctx = self.ctx

        for hook in self._resolved_data_hooks:
            hook(self, ctx)

        report.text(f'Resolved context (type: {type(ctx)}):')
        report.code(pformat(ctx), lang='python')
        report.text(f'Template (phase: {self.template.phase}):')
        report.code(self.template.text, lang='jinja')

        # 2. Render the template and context to markup text.
        try:
            extras = ExtraContextGenerator(self, host)
            report.text('Available extra context (just keys):')
            report.code(pformat(sorted(extras.names())), lang='python')
            markup = TemplateRenderer(self.template.text).render(
                ctx,
                load_extra=extras.load,
                extra_names=sorted(extras.names()),
            )
        except Exception as e:
            report = err_report()
            report.text('Failed to render Jinja template:')
            report.exception(e)
            self += report
            return

        for hook in self._markup_text_hooks:
            markup = hook(self, markup)

        report.text('Rendered markup text:')
        report.code(markup, lang='rst')

        # 3. Render the markup text to doctree nodes.
        try:
            ns, msgs = MarkupRenderer(host).render(markup, inline=self.inline)
        except Exception as e:
            report = err_report()
            report.text(
                'Failed to render markup text '
                f'to {"inline " if self.inline else ""}nodes:'
            )
            report.exception(e)
            self += report
            return

        report.text(f'Rendered nodes (inline: {self.inline}):')
        report.code('\n\n'.join([n.pformat() for n in ns]), lang='xml')
        if msgs:
            report.text('Systemd messages:')
            [report.node(msg) for msg in msgs]

        # 4. Add rendered nodes to container.
        for hook in self._rendered_nodes_hooks:
            hook(self, ns)

        # TODO: set_source_info?
        self += ns

        if self.template.debug:
            self += report

        return

    def unwrap(self) -> list[nodes.Node]:
        children = self.children
        self.clear()
        return children

    def unwrap_inline(
        self, inliner: Report.Inliner
    ) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        # Report (nodes.system_message subclass) is not inline node,
        # should be removed before inserting to doctree.
        reports = Reporter(self).clear()
        for report in reports:
            self.append(report.problematic(inliner))

        children = self.children
        self.clear()

        return children, [x for x in reports]

    def unwrap_and_replace_self(self) -> None:
        children = self.unwrap()
        # Replace self with children.
        self.replace_self(children)

    def unwrap_and_replace_self_inline(self, inliner: Report.Inliner) -> None:
        # Unwrap inline nodes and system_message noeds from node.
        ns, msgs = self.unwrap_inline(inliner)

        # Insert reports to nearst block elements (usually nodes.paragraph).
        doctree = inliner.document if isinstance(inliner, Inliner) else inliner[1]
        blkparent = find_nearest_block_element(self.parent) or doctree
        blkparent += msgs

        # Replace self with inline nodes.
        self.replace_self(ns)

    """Hooks for processing render intermediate products."""

    type UnresolvedContextHook = Callable[[pending_node, UnresolvedContext], None]
    type ResolvedContextHook = Callable[[pending_node, ResolvedContext], None]
    type MarkupTextHook = Callable[[pending_node, str], str]
    type RenderedNodesHook = Callable[[pending_node, list[nodes.Node]], None]

    _unresolved_context_hooks: list[UnresolvedContextHook]
    _resolved_data_hooks: list[ResolvedContextHook]
    _markup_text_hooks: list[MarkupTextHook]
    _rendered_nodes_hooks: list[RenderedNodesHook]

    def hook_unresolved_context(self, hook: UnresolvedContextHook) -> None:
        self._unresolved_context_hooks.append(hook)

    def hook_resolved_context(self, hook: ResolvedContextHook) -> None:
        self._resolved_data_hooks.append(hook)

    def hook_markup_text(self, hook: MarkupTextHook) -> None:
        self._markup_text_hooks.append(hook)

    def hook_rendered_nodes(self, hook: RenderedNodesHook) -> None:
        self._rendered_nodes_hooks.append(hook)

    """Methods override from parent."""

    @override
    def copy(self) -> Any:
        # NOTE: pending_node is no supposed to be copy as it does not make sense.
        #
        # For example: ablog extension may copy this node.
        if self.inline:
            return nodes.Text('')
        else:
            return nodes.paragraph()

    @override
    def deepcopy(self) -> Any:
        # NOTE: Same to :meth:`copy`.
        return self.copy()

    @override
    def astext(self) -> str:
        ctx = self.ctx
        if isinstance(ctx, UnresolvedContext):
            try:
                ctx = ctx.resolve()
            except Exception:
                return ''
        if isinstance(ctx, ParsedData):
            return ValueWrapper(ctx.content).as_str() or ''
        else:
            return ''
