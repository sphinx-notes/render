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


# ============================
# ExtraContext ABC definitions
# ============================

type ExtraContext = (
    ParsingPhaseExtraContext
    | ParsingPhaseExtraContext
    | ResolvingPhaseExtraContext
    | GlobalExtraContext
)
"""Type alias of all available extra contexts."""


class ParsingPhaseExtraContext(ABC):
    """Extra context generated during the :py:data:`~Phase.Parsing` phase.

    The ``generate`` method receives the current directive or role being executed.
    """

    @abstractmethod
    def generate(self, directive: SphinxDirective | SphinxRole) -> Any: ...


class ParsedPhaseExtraContext(ABC):
    """Extra context generated during the :py:data:`~Phase.Parsed` phase.

    The ``generate`` method receives the current Sphinx transform.
    """

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class ResolvingPhaseExtraContext(ABC):
    """Extra context generated during the :py:data:`~Phase.Resolving` phase.

    The ``generate`` method receives the current Sphinx transform.
    """

    @abstractmethod
    def generate(self, transform: SphinxTransform) -> Any: ...


class GlobalExtraContext(ABC):
    """Extra context available in all phases.

    The ``generate`` method receives the Sphinx build environment.
    """

    @abstractmethod
    def generate(self, env: BuildEnvironment) -> Any: ...


# ==========================
# Extra context registration
# ==========================


class _ExtraContextRegistry:
    ctxs: dict[str, ExtraContext]

    def __init__(self) -> None:
        self.ctxs = {}

    def is_extra_context(self, ctx: Any) -> bool:
        return isinstance(
            ctx,
            (
                ParsingPhaseExtraContext,
                ParsingPhaseExtraContext,
                ResolvingPhaseExtraContext,
                GlobalExtraContext,
            ),
        )

    def register(self, name: str, ctx: ExtraContext) -> None:
        if name in self.ctxs:
            raise ValueError(f'Extra context "{name}" already registered')
        if not self.is_extra_context(ctx):
            raise TypeError(
                f'Invalid extra context instance "{name}", Expecting {ExtraContext}'
            )
        self.ctxs[name] = ctx

    def get(self, name: str) -> ExtraContext | None:
        if name not in self.ctxs:
            return None
        return self.ctxs[name]

    def get_names_by_phase(self, cls: type) -> set[str]:
        return {name for name, ctx in self.ctxs.items() if isinstance(ctx, cls)}

    def get_names(self) -> set[str]:
        return set(self.ctxs.keys())


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
            def generate(self, directive):
                return proxy(HostWrapper(directive).doctree)

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
        requested = set(node.template.extra)
        avail = _REGISTRY.get_names()
        self.todo = requested & avail

        # Report errors for non-existent contexts
        if nonexist := requested - avail:
            self.report.text(f'Extra contexts {nonexist} are not registered.')

    def on_anytime(self, env: BuildEnvironment) -> None:
        self._generate(GlobalExtraContext, lambda ctx: ctx.generate(env))

    def on_parsing(self, directive: SphinxDirective | SphinxRole) -> None:
        self._generate(ParsingPhaseExtraContext, lambda ctx: ctx.generate(directive))

    def on_parsed(self, transform: SphinxTransform) -> None:
        self._generate(ParsedPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def on_resolving(self, transform: SphinxTransform) -> None:
        self._generate(ResolvingPhaseExtraContext, lambda ctx: ctx.generate(transform))

    def _generate(self, cls: type, gen: Callable[..., Any]) -> None:
        # Get all context names available for this phase
        avail = _REGISTRY.get_names_by_phase(cls)
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


# =====================================
# Builtin extra context implementations
# =====================================


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
    app: Sphinx

    @override
    def generate(self, env: BuildEnvironment) -> Any:
        from .utils.ctxproxy import proxy

        return proxy(self.app)


@extra_context('env')
class SphinxBuildEnvExtraContext(GlobalExtraContext):
    @override
    def generate(self, env: BuildEnvironment) -> Any:
        from .utils.ctxproxy import proxy

        return proxy(env)


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


def setup(app: Sphinx):
    SphinxExtraContext.app = app
