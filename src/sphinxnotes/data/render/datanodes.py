from __future__ import annotations
from typing import TYPE_CHECKING
from pprint import pformat

from docutils import nodes
from docutils.parsers.rst.states import Inliner

from .render import Template
from .markup import MarkupRenderer
from .template import TemplateRenderer
from ..data import RawData, PendingData, ParsedData
from ..utils import (
    Unpicklable,
    Report,
    Reporter,
    find_nearest_block_element,
)

if TYPE_CHECKING:
    from typing import Any, Callable
    from .markup import Host


class Base(nodes.Element): ...


class pending_node(Base, Unpicklable):
    # The data to be rendered by Jinja template.
    data: PendingData | ParsedData | dict[str, Any]
    # The extra context for Jina template.
    extra: dict[str, Any]
    #: Jinja template for rendering the context.
    template: Template
    #: Whether rendering to inline nodes.
    inline: bool
    #: Whether the rendering pipeline is finished (failed is also finished).
    rendered: bool

    def __init__(
        self,
        data: PendingData | ParsedData | dict[str, Any],
        tmpl: Template,
        inline: bool = False,
        rawsource='',
        *children,
        **attributes,
    ) -> None:
        super().__init__(rawsource, *children, **attributes)
        self.data = data
        self.extra = {}
        self.template = tmpl
        self.inline = inline
        self.rendered = False

        # Init hook lists.
        self._raw_data_hooks = []
        self._parsed_data_hooks = []
        self._markup_text_hooks = []
        self._rendered_nodes_hooks = []

    def render(self, host: Host) -> None:
        """
        The core function for rendering data to docutils nodes.

        1. Schema.parse(RawData) -> ParsedData
        2. TemplateRenderer.render(ParsedData) -> Markup Text (``str``)
        3. MarkupRenderer.render(Markup Text) -> doctree Nodes (list[nodes.Node])
        """

        # Make sure the function is called once.
        assert not self.rendered
        self.rendered = True

        report = Report(
            'Render Debug Report', 'DEBUG', source=self.source, line=self.line
        )

        # 1. Prepare context for Jinja template.
        if isinstance(self.data, PendingData):
            report.text('Raw data:')
            report.code(pformat(self.data.raw), lang='python')
            report.text('Schema:')
            report.code(pformat(self.data.schema), lang='python')

            for hook in self._raw_data_hooks:
                hook(self, self.data.raw)

            try:
                data = self.data = self.data.parse()
            except ValueError:
                report.text('Failed to parse raw data:')
                report.excption()
                self += report
                return
        else:
            data = self.data

        for hook in self._parsed_data_hooks:
            hook(self, data)

        report.text(f'Parsed data (type: {type(data)}):')
        report.code(pformat(data), lang='python')
        report.text('Extra context (only keys):')
        report.code(pformat(list(self.extra.keys())), lang='python')
        report.text(f'Template (phase: {self.template.phase}):')
        report.code(self.template.text, lang='jinja')

        # 2. Render the template and data to markup text.
        try:
            markup = TemplateRenderer(self.template.text).render(data, extra=self.extra)
        except Exception:
            report.text('Failed to render Jinja template:')
            report.excption()
            self += report
            return

        for hook in self._markup_text_hooks:
            markup = hook(self, markup)

        report.text('Rendered markup text:')
        report.code(markup, lang='rst')

        # 3. Render the markup text to doctree nodes.
        try:
            ns, msgs = MarkupRenderer(host).render(markup, inline=self.inline)
        except Exception:
            report.text(
                'Failed to render markup text '
                f'to {"inline " if self.inline else ""}nodes:'
            )
            report.excption()
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

        Reporter(self).clear_empty()

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

    type RawDataHook = Callable[[pending_node, RawData], None]
    type ParsedDataHook = Callable[[pending_node, ParsedData | dict[str, Any]], None]
    type MarkupTextHook = Callable[[pending_node, str], str]
    type RenderedNodesHook = Callable[[pending_node, list[nodes.Node]], None]

    _raw_data_hooks: list[RawDataHook]
    _parsed_data_hooks: list[ParsedDataHook]
    _markup_text_hooks: list[MarkupTextHook]
    _rendered_nodes_hooks: list[RenderedNodesHook]

    def hook_raw_data(self, hook: RawDataHook) -> None:
        self._raw_data_hooks.append(hook)

    def hook_parsed_data(self, hook: ParsedDataHook) -> None:
        self._parsed_data_hooks.append(hook)

    def hook_markup_text(self, hook: MarkupTextHook) -> None:
        self._markup_text_hooks.append(hook)

    def hook_rendered_nodes(self, hook: RenderedNodesHook) -> None:
        self._rendered_nodes_hooks.append(hook)
