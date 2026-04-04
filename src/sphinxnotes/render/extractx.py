from __future__ import annotations
from typing import TYPE_CHECKING, override
from abc import ABC, abstractmethod

from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform

from .render import HostWrapper
from .ctxnodes import pending_node
from .utils import find_current_section, Report, Reporter

if TYPE_CHECKING:
    from typing import Any, Callable
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


# ===================================
# ExtraContext ABC definitions
# ===================================


class ExtraContext(ABC):
    """Base class for all extra context."""


class ParsingPhaseExtraContext(ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Parsing` phase.

    The ``generate`` method receives the current directive or role being executed.
    """

    @abstractmethod
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any: ...


class ParsedPhaseExtraContext(ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Parsed` phase.

    The ``generate`` method receives the current Sphinx transform.
    """

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class ResolvingPhaseExtraContext(ExtraContext):
    """Extra context generated during the :py:data:`~Phase.Resolving` phase.

    The ``generate`` method receives the current Sphinx transform.
    """

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class GlobalExtraContext(ExtraContext):
    """Extra context available in all phases.

    The ``generate`` method receives the Sphinx build environment.
    """

    @abstractmethod
    def generate(self, env: BuildEnvironment) -> Any: ...


# =======================
# Extra context registration
# =======================


class ExtraContextRegistry:
    _extra: dict[str, ExtraContext]

    def __init__(self) -> None:
        self._extra = {}

    def register(self, name: str, ctx: ExtraContext) -> None:
        """Register an extra context.

        :param name: The context name, used in templates via ``load('name')``.
        :param ctx: The extra context instance.
        """
        if name in self._extra:
            raise ValueError(f'Extra context "{name}" already registered')
        self._extra[name] = ctx

    def get(self, name: str) -> ExtraContext | None:
        """Get a registered extra context by name."""
        return self._extra.get(name)

    @property
    def names(self) -> list[str]:
        """Return all registered extra context names."""
        return list(self._extra.keys())


# Global registry instance
REGISTRY = ExtraContextRegistry()


def extra_context(name: str):
    """Decorator to register an extra context.

    The phase is determined by which ExtraContext subclass is used:

    - :py:class:`GlobalExtraContext` -> available in all phases
    - :py:class:`ParsingPhaseExtraContext` -> available during Parsing phase
    - :py:class:`ParsedPhaseExtraContext` -> available during Parsed phase
    - :py:class:`ResolvingPhaseExtraContext` -> available during Resolving phase

    Example::

        @extra_context('doc')
        class DocExtraContext(ParsingPhaseExtraContext):
            def generate(self, directive):
                return proxy(HostWrapper(directive).doctree)

    :param name: The context name, used in templates via ``load('name')``.
    """

    def decorator(cls):
        if not issubclass(cls, ExtraContext):
            raise TypeError(f'{cls.__name__} must subclass an ExtraContext ABC')

        instance = cls()
        REGISTRY.register(name, instance)
        return cls

    return decorator


# ===================================
# Builtin extra context implementations
# ===================================


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
        from .utils.ctxproxy import proxy

        return proxy(HostWrapper(directive).doctree)


@extra_context('section')
class SectionExtraContext(ParsingPhaseExtraContext):
    @override
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any:
        from .utils.ctxproxy import proxy

        parent = HostWrapper(directive).parent
        return proxy(find_current_section(parent))


@extra_context('sphinx')
class SphinxExtraContext(GlobalExtraContext):
    @override
    def generate(self, env: BuildEnvironment) -> Any:
        from .utils.ctxproxy import proxy

        return proxy(env.app)


@extra_context('docutils')
class DocutilsExtraContext(GlobalExtraContext):
    @override
    def generate(self, env: BuildEnvironment) -> Any:
        from docutils.parsers.rst.directives import _directives
        from docutils.parsers.rst.roles import _roles

        return {
            'directives': _directives,
            'roles': _roles,
        }


# ========================
# Extra Context Generation
# ========================


class ExtraContextGenerator:
    node: pending_node
    report: Report

    def __init__(self, node: pending_node) -> None:
        self.node = node
        self.report = Report(
            'Extra Context Generation Report',
            'ERROR',
            source=node.source,
            line=node.line,
        )
        Reporter(node).append(self.report)

    def on_anytime(self, env: BuildEnvironment) -> None:
        """Generate global extra context for requested names."""
        self._generate(GlobalExtraContext, lambda ctx: ctx.generate(env))

    def on_parsing(self, directive: SphinxDirective | SphinxRole) -> None:
        """Generate parsing phase extra context for requested names."""
        self._generate(ParsingPhaseExtraContext, lambda ctx: ctx.generate(directive))

    def on_parsed(self, transform: SphinxTransform) -> None:
        """Generate parsed phase extra context for requested names."""
        self._generate(ParsedPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def on_resolving(self, transform: SphinxTransform) -> None:
        """Generate resolving phase extra context for requested names."""
        self._generate(ResolvingPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def _generate(self, cls: type, gen: Callable[[ExtraContext], Any]) -> None:
        """Generate extra context of the given type for all requested names."""
        for name in self.node.template.extra:
            ctx = REGISTRY.get(name)
            if ctx is None:
                self.report.text(
                    f'Extra context "{name}" is not registered. '
                    f'Available: {REGISTRY.names}'
                )
                continue
            if not isinstance(ctx, cls):
                self.report.text(
                    f'Extra context "{name}" has wrong type: '
                    f'expected {cls.__name__}, got {type(ctx).__name__}'
                )
                continue
            try:
                self.node.extra[name] = gen(ctx)
            except Exception:
                self.report.text(f'Failed to generate extra context "{name}":')
                self.report.traceback()


def setup(app: Sphinx):
    pass
