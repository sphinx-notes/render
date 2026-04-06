from __future__ import annotations
from typing import TYPE_CHECKING, ClassVar
from abc import ABC, abstractmethod

from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform

from .template import Phase
from .ctxnodes import pending_node
from .utils import Report, Reporter

if TYPE_CHECKING:
    from typing import Any, Callable
    from sphinx.environment import BuildEnvironment

# ============================
# ExtraContext ABC definitions
# ============================


class _ExtraContext(ABC):
    """Base class of extra context."""

    phase: ClassVar[Phase | None] = None

    @abstractmethod
    def generate(self, *args, **kwargs) -> Any: ...


class ParsingPhaseExtraContext(_ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Parsing` phase.
    The ``generate`` method receives the current directive or role being executed.
    """

    phase = Phase.Parsing

    @abstractmethod
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any: ...


class ParsedPhaseExtraContext(_ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Parsed` phase.
    The ``generate`` method receives the current Sphinx transform.
    """

    phase = Phase.Parsed

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class ResolvingPhaseExtraContext(_ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Resolving` phase.
    The ``generate`` method receives the current Sphinx transform.
    """

    phase = Phase.Resolving

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class GlobalExtraContext(_ExtraContext):
    """Extra context available in all phases.
    The ``generate`` method receives the Sphinx build environment.
    """

    phase = None

    @abstractmethod
    def generate(self, env: BuildEnvironment) -> Any: ...


# ==========================
# Extra context registration
# ==========================


class _ExtraContextRegistry:
    ctxs: dict[str, _ExtraContext]

    def __init__(self) -> None:
        self.ctxs = {}

    def register(self, name: str, ctx: _ExtraContext) -> None:
        if name in self.ctxs:
            raise ValueError(f'Extra context "{name}" already registered')
        self.ctxs[name] = ctx

    def get(self, name: str) -> _ExtraContext | None:
        if name not in self.ctxs:
            return None
        return self.ctxs[name]

    def get_names(self) -> set[str]:
        return set(self.ctxs.keys())

    def get_names_at_phase(self, phase: Phase | None) -> set[str]:
        return {name for name, ctx in self.ctxs.items() if ctx.phase == phase}

    def get_names_before_phase(self, phase: Phase | None) -> set[str]:
        return {
            name
            for name, ctx in self.ctxs.items()
            if phase is None or ctx.phase is None or phase >= ctx.phase
        }


# Global registry instance.
_REGISTRY = _ExtraContextRegistry()


def extra_context(name: str):
    """Decorator to register an extra context.

    The phase is determined by which ExtraContext class is used:

    :py:class:`GlobalExtraContext`
        available in all phases
    :py:class:`ParsingPhaseExtraContext`
        available during Parsing phase
    :py:class:`ParsedPhaseExtraContext`
        available during Parsed phase
    :py:class:`ResolvingPhaseExtraContext`
        available during Resolving phase

    Example::

        @extra_context('doc')
        class DocExtraContext(ParsingPhaseExtraContext):
            def generate(self, ctx):
                return proxy(HostWrapper(ctx).doctree)

    :param name: The context name, used in templates via ``load_extra('name')``.
    """

    def decorator(cls):
        _REGISTRY.register(name, cls())
        return cls

    return decorator


# ========================
# Extra Context Generation
# ========================


class ExtraContextGenerator:
    node: pending_node
    todo: set[str]
    report: Report

    env: ClassVar[BuildEnvironment]

    def __init__(self, node: pending_node) -> None:
        self.node = node
        self.report = Report(
            'Extra Context Generation Report',
            'ERROR',
            source=node.source,
            line=node.line,
        )
        Reporter(node).append(self.report)

        # Initialize todo with requested extra contexts, validate they exist
        total = _REGISTRY.get_names()
        avail = _REGISTRY.get_names_before_phase(node.template.phase)
        requested = set(node.template.extra)
        self.todo = requested & avail

        # Report errors for non-existent contexts
        if nonexist := requested - total:
            self.report.text(f'Extra contexts {nonexist} are non-exist.')
        if nonavail := requested & total - avail:
            self.report.text(
                f'Extra contexts {nonavail} are not available '
                f'at pahse {node.template.phase}.'
            )

    def on_anytime(self, env: BuildEnvironment) -> None:
        self._generate(GlobalExtraContext, lambda ctx: ctx.generate(env))

    def on_parsing(self, directive: SphinxDirective | SphinxRole) -> None:
        self._generate(ParsingPhaseExtraContext, lambda ctx: ctx.generate(directive))

    def on_parsed(self, transform: SphinxTransform) -> None:
        self._generate(ParsedPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def on_resolving(self, transform: SphinxTransform) -> None:
        self._generate(ResolvingPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def _generate(self, cls: type[_ExtraContext], gen: Callable[..., Any]) -> None:
        # Get all context names available for this phase
        avail = _REGISTRY.get_names_at_phase(cls.phase)
        # Find which ones are requested and not yet generated
        todo = avail & self.todo

        for name in todo:
            ctx = _REGISTRY.get(name)
            if ctx is None:
                continue
            try:
                self.node.extra[name] = gen(ctx)
                self.todo.discard(name)
            except Exception:
                self.report.text(f'Failed to generate extra context "{name}":')
                self.report.traceback()
