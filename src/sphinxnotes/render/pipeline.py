"""
sphinxnotes.render.pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This module defines pipeline for rendering data to nodes.

The Pipline
===========

1. Define context: BaseDataSource generates a :class:`pending_node`, which contains:

   - Context
   - Template for rendering data to markup text
   - Possible extra contexts

   See also :class:`BaseDataSource`.

2. Render data: the ``pending_node`` nodes will be rendered
   (by calling :meth:`pending_node.render`) at some point, depending on
   :attr:`pending_node.template.phase`.

   The one who calls ``pending_node.render`` is called ``Host``.
   The ``Host`` host is responsible for rendering the markup text into docutils
   nodes (See :class:`MarkupRenderer`).

   Phases:

   :``Phase.Parsing``:
      Called by BaseDataSource ('s subclasses)

   :``Phase.Parsed``:
      Called by :class:`ParsedHookTransform`.

   :``Phase.Resolving``:
      Called by :class:`ResolvingHookTransform`.

How context be rendered ``list[nodes.Node]``
============================================

.. seealso:: :meth:`.ctxnodes.pending_node.render`.

"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, final, cast
from abc import abstractmethod, ABC

from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform, ReferencesResolver

from .render import HostWrapper, Phase, Template, Host, ParseHost, TransformHost
from .ctx import PendingContext, ResolvedContext
from .ctxnodes import pending_node
from .extractx import ExtraContextGenerator


if TYPE_CHECKING:
    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


class Pipeline(ABC):
    """
    The core class defines the pipleing of rendering :class:`pending_node`s.

    Subclass is responsible to:

    - call ``queue_xxx`` to add pendin nodes into queue.
    - override :meth:`process_pending_node` to control when a pending node gets
      rendered. In this method subclass can also call ``queue_xxx`` to add more
      pending nodes.
    - call :meth:`render_queue` to process all queued nodes and
      returns any that couldn't be rendered in the current phase.

    See Also:

    - :class:`BaseDataSource`: Context source implementation and hook for Phase.Parsing
    - :class:`ParsedHookTransform`: Built-in hook for Phase.Parsed
    - :class:`ResolvingHookTransform`: Built-in hook for Phase.Resolving
    """

    #: Queue of pending node to be rendered.
    _q: list[pending_node] | None = None

    """Methods to be overrided."""

    def process_pending_node(self, n: pending_node) -> bool:
        """
        You can add hooks to pending node here.

        Return ``true`` if you want to render the pending node *now*,
        otherwise it will be inserted to doctree directly andwaiting to later
        rendering
        """
        ...

    """Helper method for subclasses."""

    @final
    def queue_pending_node(self, n: pending_node) -> None:
        if not self._q:
            self._q = []
        self._q.append(n)

    @final
    def queue_context(
        self, ctx: PendingContext | ResolvedContext, tmpl: Template
    ) -> pending_node:
        pending = pending_node(ctx, tmpl)
        self.queue_pending_node(pending)
        return pending

    @final
    def render_queue(self) -> list[pending_node]:
        """
        Try rendering all pending nodes in queue.

        If the timing(Phase) is ok, :class:`pending_node` will be rendered
        (pending.rendered = True); otherwise, the pending node is unchanged.

        If the pending node is already inserted to document, it will not be return.
        And the corrsponding rendered node will replace it too.
        """

        logger.debug(
            f'{type(self)} is running its render queue, '
            f'{len(self._q or [])} node(s) to render'
        )
        ns = []
        while self._q:
            pending = self._q.pop()

            ok = self.process_pending_node(pending)
            logger.debug(
                f'{type(self)} is trying to render '
                f'{pending.source}:{pending.line}, ok? {ok}'
            )

            if not ok:
                ns.append(pending)
                continue

            # Generate global extra context for later use.
            ExtraContextGenerator(pending).on_anytime()

            host = cast(Host, self)
            pending.render(host)

            if pending.parent is None:
                ns.append(pending)
                continue

            if pending.inline:
                host_ = HostWrapper(host)
                pending.unwrap_and_replace_self_inline((host_.doctree, pending.parent))
            else:
                pending.unwrap_and_replace_self()

        logger.debug(
            f'{type(self)} runs out of its render queue, '
            f'{len(self._q or [])} node(s) hanging'
        )

        return ns


class BaseContextSource(Pipeline):
    """
    Abstract base class for generateing context, as the source of the rendering
    pipeline.

    This class also responsible to render context in Phase.Parsing. So the final
    implementations MUST be subclass of :class:`SphinxDirective` or
    :class:`SphinxRole`, which provide the execution context and interface for
    processing reStructuredText markup.
    """

    """Methods to be implemented."""

    @abstractmethod
    def current_context(self) -> PendingContext | ResolvedContext:
        """Return the context to be rendered."""
        ...

    @abstractmethod
    def current_template(self) -> Template:
        """
        Return the template for rendering the context.

        This method should be implemented to provide the Jinja2 template
        that will render the context into markup text. The template determines
        the phase at which rendering occurs.

        Returns:
            The template to use for rendering.
        """
        ...

    """Methods override from parent."""

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        host = cast(ParseHost, self)

        # Set source and line.
        host.set_source_info(n)
        # Generate and save parsing phase extra context for later use.
        ExtraContextGenerator(n).on_parsing(host)

        return n.template.phase == Phase.Parsing


class BaseContextDirective(BaseContextSource, SphinxDirective):
    @override
    def run(self) -> list[nodes.Node]:
        self.queue_context(self.current_context(), self.current_template())

        ns = []
        for x in self.render_queue():
            if not x.rendered:
                ns.append(x)
                continue
            ns += x.unwrap()

        return ns


class BaseContextRole(BaseContextSource, SphinxRole):
    @override
    def process_pending_node(self, n: pending_node) -> bool:
        n.inline = True
        return super().process_pending_node(n)

    @override
    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        pending = self.queue_context(self.current_context(), self.current_template())
        pending.inline = True

        ns, msgs = [], []
        for n in self.render_queue():
            if not n.rendered:
                ns.append(n)
                continue
            ns_, msgs_ = n.unwrap_inline(self.inliner)
            ns += ns_
            msgs += msgs_

        return ns, msgs


class ParsedHookTransform(SphinxTransform, Pipeline):
    # Before almost all others.
    default_priority = 100

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        ExtraContextGenerator(n).on_parsed(cast(TransformHost, self))
        return n.template.phase == Phase.Parsed

    @override
    def apply(self, **kwargs):
        for pending in self.document.findall(pending_node):
            self.queue_pending_node(pending)

        for n in self.render_queue():
            ...


class ResolvingHookTransform(SphinxPostTransform, Pipeline):
    # After resolving pending_xref
    default_priority = (ReferencesResolver.default_priority or 10) + 5

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        ExtraContextGenerator(n).on_post_transform(cast(TransformHost, self))
        return n.template.phase == Phase.Resolving

    @override
    def apply(self, **kwargs):
        for pending in self.document.findall(pending_node):
            self.queue_pending_node(pending)
        ns = self.render_queue()

        # NOTE: Should no node left.
        assert len(ns) == 0


def setup(app: Sphinx) -> None:
    # Hook for Phase.Parsed.
    app.add_transform(ParsedHookTransform)

    # Hook for Phase.Resolving.
    app.add_post_transform(ResolvingHookTransform)
