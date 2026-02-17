from typing import TYPE_CHECKING, override
from pprint import pformat

from docutils import nodes
from docutils.parsers.rst.states import Inliner

from .render import Template
from .ctx import PendingContextRef, PendingContext, PendingContextStorage, ResolvedContext
from .markup import MarkupRenderer
from .template import TemplateRenderer
from .utils import (
    Report,
    Reporter,
    find_nearest_block_element,
)

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar
    from .markup import Host


class pending_node(nodes.Element):
    # The context to be rendered by Jinja template.
    ctx: PendingContextRef | ResolvedContext
    # The extra context as supplement to ctx.
    extra: dict[str, Any]
    #: Jinja template for rendering the context.
    template: Template
    #: Whether rendering to inline nodes.
    inline: bool
    #: Whether the rendering pipeline is finished (failed is also finished).
    rendered: bool

    #: Mapping of PendingContextRef -> PendingContext.
    #:
    #: NOTE: ``PendingContextStorage`` holds Unpicklable data (``PendingContext``)
    #: but it is doesn't matters :-), cause pickle doesn't deal with ClassVar.
    _PENDING_CONTEXTS: ClassVar[PendingContextStorage] = PendingContextStorage()

    def __init__(
        self,
        ctx: PendingContext | PendingContextRef | ResolvedContext,
        tmpl: Template,
        inline: bool = False,
        rawsource='',
        *children,
        **attributes,
    ) -> None:
        super().__init__(rawsource, *children, **attributes)
        if not isinstance(ctx, PendingContext):
            self.ctx = ctx
        else:
            self.ctx = self._PENDING_CONTEXTS.stash(ctx)
        self.extra = {}
        self.template = tmpl
        self.inline = inline
        self.rendered = False

        # Init hook lists.
        self._pending_context_hooks = []
        self._resolved_data_hooks = []
        self._markup_text_hooks = []
        self._rendered_nodes_hooks = []

    def render(self, host: Host) -> None:
        """
        The core function for rendering context to docutils nodes.

        1. PendingContextRef -> PendingContext -> ResolvedContext
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

        # 1. Prepare context for Jinja template.
        if isinstance(self.ctx, PendingContextRef):
            report.text('Pending context ref:')
            report.code(pformat(self.ctx), lang='python')

            pdata = self._PENDING_CONTEXTS.retrieve(self.ctx)
            if pdata is None:
                report = err_report()
                report.text(f'Failed to retrieve pending context from ref {self.ctx}')
                self += report
                return None

            report.text('Pending context:')
            report.code(pformat(pdata), lang='python')

            for hook in self._pending_context_hooks:
                hook(self, pdata)

            try:
                ctx = self.ctx = pdata.resolve()
            except Exception as e:
                report = err_report()
                report.text('Failed to resolve pending context:')
                report.exception(e)
                self += report
                return None
        else:
            ctx = self.ctx

        for hook in self._resolved_data_hooks:
            hook(self, ctx)

        report.text(f'Resolved context (type: {type(ctx)}):')
        report.code(pformat(ctx), lang='python')
        report.text('Extra context (only keys):')
        report.code(pformat(list(self.extra.keys())), lang='python')
        report.text(f'Template (phase: {self.template.phase}):')
        report.code(self.template.text, lang='jinja')

        # 2. Render the template and context to markup text.
        try:
            markup = TemplateRenderer(self.template.text).render(ctx, extra=self.extra)
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

    """Hooks for procssing render intermediate products. """

    type PendingContextHook = Callable[[pending_node, PendingContext], None]
    type ResolvedContextHook = Callable[[pending_node, ResolvedContext], None]
    type MarkupTextHook = Callable[[pending_node, str], str]
    type RenderedNodesHook = Callable[[pending_node, list[nodes.Node]], None]

    _pending_context_hooks: list[PendingContextHook]
    _resolved_data_hooks: list[ResolvedContextHook]
    _markup_text_hooks: list[MarkupTextHook]
    _rendered_nodes_hooks: list[RenderedNodesHook]

    def hook_pending_context(self, hook: PendingContextHook) -> None:
        self._pending_context_hooks.append(hook)

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
