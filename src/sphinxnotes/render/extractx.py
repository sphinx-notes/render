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
    phase: Phase
    node: pending_node
    env: BuildEnvironment
    host: SphinxDirective | SphinxRole | SphinxTransform


class ExtraContext(ABC):
    """Base class of extra context."""

    @abstractmethod
    def generate(self, request: ExtraContextRequest) -> Any: ...


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
    """Decorator to register an extra context.

    Example::

        @extra_context('doc')
        class DocExtraContext(ExtraContext):
            def generate(self, request):
                return proxy(request.host.document)

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
    request: ExtraContextRequest
    cache: dict[str, Any]

    def __init__(
        self,
        node: pending_node,
        host: SphinxDirective | SphinxRole | SphinxTransform,
    ) -> None:
        self.node = node
        self.request = ExtraContextRequest(node.template.phase, node, host.env, host)
        self.cache = {}

    def names(self) -> set[str]:
        return _REGISTRY.get_names()

    def load(self, name: str) -> Any:
        if name in self.cache:
            return self.cache[name]

        ctx = _REGISTRY.get(name)
        if ctx is None:
            raise ValueError(
                f'Extra context "{name}" is not registered. '
                f'Available: {sorted(self.names())}'
            )

        value = ctx.generate(self.request)
        self.cache[name] = value
        return value
