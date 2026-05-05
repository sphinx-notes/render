"""This module defines pipeline for rendering data to nodes."""

from __future__ import annotations
from typing import TYPE_CHECKING, override, final, cast
from abc import abstractmethod, ABC

from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform, ReferencesResolver

from .template import HostWrapper, Phase, Template, Host
from .ctx import UnresolvedContext, ResolvedContext
from .ctxnodes import pending_node
if TYPE_CHECKING:
    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


class Pipeline(ABC):
    """
    The core class defines the pipeline for rendering
    :py:class:`~sphinxnotes.render.pending_node`.

    Subclasses are responsible for:

    - calling ``queue_xxx`` to add pending nodes into the queue.
    - overriding :py:meth:`~Pipeline.process_pending_node` to control when a
      pending node gets rendered. In this method, subclasses can also call
      ``queue_xxx`` to add more pending nodes.
    - calling ``render_queue`` to process all queued nodes and return any that
      could not be rendered in the current phase.

    .. seealso::

       - :py:class:`BaseContextSource`: Class for generating
         :py:class:`sphinxnotes.render.pending_node` and hook of
         :py:data:`~sphinxnotes.render.Phase.Parsing` render phase
       - :py:class:`ParsedHookTransform`: Built-in hook for
         :py:data:`~sphinxnotes.render.Phase.Parsed` render phase
       - :py:class:`ResolvingHookTransform`: Built-in hook for
         :py:data:`~sphinxnotes.render.Phase.Resolving` render phase
    """

    #: Queue of pending nodes to be rendered.
    _q: list[pending_node] | None = None

    """Methods to be overridden."""

    def process_pending_node(self, n: pending_node) -> bool:
        """
        This method is called when it is the pending node's turn to be rendered.

        Return ``true`` if you want to render the pending node *now*;
        otherwise it will be inserted into the doctree directly and wait for
        later rendering (and this method will be called again.).

        You can add hooks to the pending node here, or call
        :py:meth:`~Pipeline.queue_pending_node`. You are responsible for
        inserting created nodes into the doctree yourself.

        .. note::

           Please always call ``super().process_pending_node(n)`` to ensure the
           extension functions properly.
        """
        ...

    """Helper method for subclasses."""

    @final
    def queue_pending_node(self, n: pending_node) -> None:
        """Push back a new :py:class:`~sphinxnotes.render.pending_node` to the
        render queue."""
        if not self._q:
            self._q = []
        self._q.append(n)

    @final
    def queue_context(
        self, ctx: UnresolvedContext | ResolvedContext, tmpl: Template
    ) -> pending_node:
        """A helper method for ``queue_pending_node``."""
        pending = pending_node(ctx, tmpl)
        self.queue_pending_node(pending)
        return pending

    @final
    def render_queue(self) -> list[pending_node]:
        """
        Try rendering all pending nodes in queue.

        If the timing (Phase) is appropriate, :py:class:`sphinxnotes.render.pending_node`
        will be rendered (pending.rendered = True); otherwise, the pending node
        is unchanged.

        If the pending node is already inserted into the document, it will not be returned.
        The corresponding rendered node will replace it.
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

            host = cast(Host, self)

            # Perform render.
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
    Abstract base class for generating context, as the source of the rendering
    pipeline.

    This class is also responsible for rendering context in :py:data:`Phase.Parsing`.
    So the final implementations **MUST** be a subclass of
    :py:class:`~sphinx.util.docutils.SphinxDirective` or
    :py:class:`~sphinx.util.docutils.SphinxRole`, which provide the execution
    context and interface for processing reStructuredText markup.
    """

    """Methods to be implemented."""

    @abstractmethod
    def current_context(self) -> UnresolvedContext | ResolvedContext:
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
        host = cast(SphinxDirective | SphinxRole, self)
        # Set source and line.
        host.set_source_info(n)
        return n.template.phase == Phase.Parsing


class BaseContextDirective(BaseContextSource, SphinxDirective):
    """This class generates :py:class:`sphinxnotes.render.pending_node` in
    ``SphinxDirective.run()`` method and makes sure it is rendered correctly.

    User should implement ``current_context`` and ``current_template`` methods
    to provide the constructor parameters of ``pending_node``.
    """

    @final
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
    """This class generates :py:class:`sphinxnotes.render.pending_node` in
    ``SphinxRole.run()`` method and makes sure it is rendered correctly.

    User should implement ``current_context`` and ``current_template`` methods
    to provide the constructor parameters of ``pending_node``.
    """

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        n.inline = True
        return super().process_pending_node(n)

    @final
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


class _ParsedHookTransform(SphinxTransform, Pipeline):
    # Before almost all others.
    default_priority = 100

    @override
    def process_pending_node(self, n: pending_node) -> bool:
        return n.template.phase == Phase.Parsed

    @override
    def apply(self, **kwargs):
        for pending in self.document.findall(pending_node):
            self.queue_pending_node(pending)

        for n in self.render_queue():
            ...


class _ResolvingHookTransform(SphinxPostTransform, Pipeline):
    # After resolving pending_xref
    default_priority = (ReferencesResolver.default_priority or 10) + 5

    @override
    def process_pending_node(self, n: pending_node) -> bool:
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
    app.add_transform(_ParsedHookTransform)

    # Hook for Phase.Resolving.
    app.add_post_transform(_ResolvingHookTransform)
