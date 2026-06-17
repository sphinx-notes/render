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
    def generate(self, req: ExtraContextRequest, *args, **kwargs) -> Any: ...


# ==========================
# Extra context registration
# ==========================


class ExtraContextRegistry:
    """Registry for extra contexts."""

    _ctxs: dict[str, ExtraContext]

    def __init__(self) -> None:
        self._ctxs = {}

    def add(self, name: str, ctx: ExtraContext) -> None:
        """Register an extra context.

        :param name: The context name, used in templates via ``load_extra('name')``
        :param ctx: An :py:class:`ExtraContext` instance

        .. note:: Using the :py:deco:`extra_context` decorator is recommended for most cases.
        """
        if name in self._ctxs:
            raise ValueError(f'Extra context "{name}" already registered')
        self._ctxs[name] = ctx


REGISTRY = ExtraContextRegistry()
"""The global registry for extra contexts.

This is the underlying registry used by the :py:func:`extra_context` decorator.
Using the decorator is recommended for most cases, but you can also register
extra contexts directly via this registry.
"""


def extra_context(name: str):
    """Decorator to register an :py:class:`ExtraContext`.

    :param name: The context name, used in templates via ``load_extra('name')``.
    """

    def decorator(cls):
        REGISTRY.add(name, cls())
        return cls

    return decorator


def extra_context_names() -> set[str]:
    return set(REGISTRY._ctxs.keys())


def extra_context_loader(request: ExtraContextRequest):
    def load_extra(name: str, *args, **kwargs) -> Any:
        ctx = REGISTRY._ctxs.get(name)
        if ctx is None:
            raise ValueError(
                f'Extra context "{name}" is not registered. '
                f'Available: {sorted(extra_context_names())}'
            )

        try:
            return ctx.generate(request, *args, **kwargs)
        except Exception as e:
            raise ValueError(f'Failed to load extra context "{name}".') from e

    return load_extra
