from __future__ import annotations
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform

from .template import Phase

if TYPE_CHECKING:
    from typing import Any
    from sphinx.environment import BuildEnvironment
    from .ctxnodes import pending_node


@dataclass(frozen=True)
class ExtraContextRequest:
    #: The render phase of the current template.
    phase: Phase
    #: The pending node being rendered.
    node: pending_node
    #: The current Sphinx build environment.
    env: BuildEnvironment
    #: The Sphinx execution object associated with this render:
    #: a :py:class:`~sphinx.util.docutils.SphinxDirective` or
    #: :py:class:`~sphinx.util.docutils.SphinxRole` during :py:data:`Phase.Parsing`,
    #: or a :py:class:`~sphinx.transforms.SphinxTransform` during later phases.
    host: SphinxDirective | SphinxRole | SphinxTransform


class ExtraContext(ABC):
    """Base class of extra context."""

    @abstractmethod
    def generate(self, req: ExtraContextRequest) -> Any: ...


# ==========================
# Extra context registration
# ==========================


class _ExtraContextRegistry:
    ctxs: dict[str, ExtraContext]

    def __init__(self) -> None:
        self.ctxs = {}

    def register(self, name: str, ctx: ExtraContext) -> None:
        if name in self.ctxs:
            raise ValueError(f'Extra context "{name}" already registered')
        self.ctxs[name] = ctx

    def get(self, name: str) -> ExtraContext | None:
        if name not in self.ctxs:
            return None
        return self.ctxs[name]

    def get_names(self) -> set[str]:
        return set(self.ctxs.keys())


_REGISTRY = _ExtraContextRegistry()


def extra_context(name: str):
    """Decorator to register an :py:class:`ExtraContext`.

    :param name: The context name, used in templates via ``load_extra('name')``.
    """

    def decorator(cls):
        _REGISTRY.register(name, cls())
        return cls

    return decorator


def extra_context_names() -> set[str]:
    return _REGISTRY.get_names()


def extra_context_loader(request: ExtraContextRequest):
    def load_extra(name: str) -> Any:
        ctx = _REGISTRY.get(name)
        if ctx is None:
            raise ValueError(
                f'Extra context "{name}" is not registered. '
                f'Available: {sorted(extra_context_names())}'
            )

        return ctx.generate(request)

    return load_extra
