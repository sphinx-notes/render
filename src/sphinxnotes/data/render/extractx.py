from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, override
from abc import ABC, abstractmethod

from docutils import nodes
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.transforms import SphinxTransform

from ..utils import find_current_section
from ..utils.ctxproxy import proxy
from .renderer import Host, ParseHost

if TYPE_CHECKING:
    from typing import Any, Callable, ClassVar


from ..utils import Report
from .nodes import pending_data
from .renderer import TransformHost
from .reporter import Reporter


class ExtraContxt(ABC):
    """Base class for extra context generator in different render phase."""

    ...


class RenderPhaseExtraContext(ExtraContxt):
    @abstractmethod
    def generate(self, host: Host) -> Any: ...


class ParsePhaseExtraContext(ExtraContxt):
    @abstractmethod
    def generate(self, host: ParseHost) -> Any: ...


class TransformPhaseExtraContext(ExtraContxt):
    @abstractmethod
    def generate(self, host: TransformHost) -> Any: ...


# ======================================
# Extra context registion and management
# ======================================


class ExtraContextRegistry:
    names: set[str]
    parsing: dict[str, ParsePhaseExtraContext]
    parsed: dict[str, ParsePhaseExtraContext]
    post_transform: dict[str, TransformPhaseExtraContext]
    render: dict[str, RenderPhaseExtraContext]

    def __init__(self) -> None:
        self.names = set()
        self.parsing = {}
        self.parsed = {}
        self.post_transform = {}
        self.render = {}

        self.add_parsing_phase_extra_context('markup', _MarkupExtraContext())
        self.add_parsing_phase_extra_context('section', _SectionExtraContext())
        self.add_render_phase_extra_context('doc', _DocExtraContext())
        self.add_render_phase_extra_context('env', _SphinxEnvExtraContext())
        self.add_render_phase_extra_context('config', _SphinxConfigExtraContext())

    def _name_dedup(self, name: str) -> None:
        # TODO: allow dup
        if name in self.names:
            raise ValueError(f'Context generator {name} already exists')
        self.names.add(name)

    def add_parsing_phase_extra_context(
        self, name: str, ctxgen: ParsePhaseExtraContext
    ) -> None:
        self._name_dedup(name)
        self.parsing['_' + name] = ctxgen

    def add_parsed_phase_extra_context(
        self, name: str, ctxgen: ParsePhaseExtraContext
    ) -> None:
        self._name_dedup(name)
        self.parsed['_' + name] = ctxgen

    def add_post_transform_phase_extra_context(
        self, name: str, ctxgen: TransformPhaseExtraContext
    ) -> None:
        self._name_dedup(name)
        self.post_transform['_' + name] = ctxgen

    def add_render_phase_extra_context(
        self, name: str, ctxgen: RenderPhaseExtraContext
    ):
        self._name_dedup(name)
        self.render['_' + name] = ctxgen


class ExtraContextGenerator:
    node: pending_data
    report: Report

    registry: ClassVar[ExtraContextRegistry] = ExtraContextRegistry()

    def __init__(self, node: pending_data) -> None:
        self.node = node
        self.report = Report('Extra Context Generation Report', 'ERROR')
        Reporter(node).append(self.report)

    def on_rendering(self, host: Host) -> None:
        for name, ctxgen in self.registry.render.items():
            self._safegen(name, lambda: ctxgen.generate(host))

    def on_parsing(self, host: ParseHost) -> None:
        for name, ctxgen in self.registry.parsing.items():
            self._safegen(name, lambda: ctxgen.generate(host))

    def on_parsed(self, host: ParseHost) -> None:
        for name, ctxgen in self.registry.parsed.items():
            self._safegen(name, lambda: ctxgen.generate(host))

    def on_post_transform(self, host: TransformHost) -> None:
        for name, ctxgen in self.registry.post_transform.items():
            self._safegen(name, lambda: ctxgen.generate(host))

    def _safegen(self, name: str, gen: Callable[[], Any]):
        try:
            # ctxgen.generate can be user-defined code, exception of any kind are possible.
            self.node.extra[name] = gen()
        except Exception:
            self.report.text(f'Failed to generate extra context {name}:')
            self.report.excption()


# ===================================
# Bulitin extra context implementions
# ===================================


@dataclass
class _Host:
    v: Host

    @property
    def doctree(self) -> nodes.document:
        if isinstance(self.v, SphinxDirective):
            return self.v.state.document
        elif isinstance(self.v, SphinxRole):
            return self.v.inliner.document
        elif isinstance(self.v, SphinxTransform):
            return self.v.document
        else:
            raise NotImplementedError

    @property
    def parent(self) -> nodes.Element | None:
        if isinstance(self.v, SphinxDirective):
            return self.v.state.parent
        elif isinstance(self.v, SphinxRole):
            return self.v.inliner.parent
        else:
            return None


class _MarkupExtraContext(ParsePhaseExtraContext):
    @override
    def generate(self, host: ParseHost) -> Any:
        isdir = isinstance(host, SphinxDirective)
        return {
            'type': 'directive' if isdir else 'role',
            'name': host.name,
            'lineno': host.lineno,
            'rawtext': host.block_text if isdir else host.rawtext,
        }


class _DocExtraContext(RenderPhaseExtraContext):
    @override
    def generate(self, host: Host) -> Any:
        return proxy(_Host(host).doctree)


class _SectionExtraContext(ParsePhaseExtraContext):
    @override
    def generate(self, host: ParseHost) -> Any:
        parent = _Host(host).parent
        return proxy(find_current_section(parent))


class _SphinxEnvExtraContext(RenderPhaseExtraContext):
    @override
    def generate(self, host: Host) -> Any:
        return proxy(host.env)


class _SphinxConfigExtraContext(RenderPhaseExtraContext):
    @override
    def generate(self, host: Host) -> Any:
        return proxy(host.config)
