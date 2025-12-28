from __future__ import annotations
import dataclasses
from pprint import pformat
from typing import Any, Callable
from enum import Enum

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging
from sphinx.application import Sphinx
from sphinx.builders import Builder

from jinja2.sandbox import SandboxedEnvironment

from .data import Data

logger = logging.getLogger(__name__)


class JinjaEnv(SandboxedEnvironment):
    _builder: Builder
    # List of user defined filter factories.
    _filter_factories = {}

    @classmethod
    def setup(cls, app: Sphinx):
        """You must call this method before instantiating"""
        app.connect('builder-inited', cls._on_builder_inited)
        app.connect('build-finished', cls._on_build_finished)

    @classmethod
    def _on_builder_inited(cls, app: Sphinx):
        cls._builder = app.builder

    @classmethod
    def add_filter(cls, name: str, ff):
        cls._filter_factories[name] = ff

    @classmethod
    def _on_build_finished(cls, app: Sphinx, exception): ...

    def is_safe_attribute(self, obj, attr, value=None):
        """
        The sandboxed environment will call this method to check if the
        attribute of an object is safe to access. Per default all attributes
        starting with an underscore are considered private as well as the
        special attributes of internal python objects as returned by the
        is_internal_attribute() function.
        """
        if attr.startswith('_'):
            return False
        return super().is_safe_attribute(obj, attr, value)

    def __init__(self):
        super().__init__(
            extensions=[
                'jinja2.ext.loopcontrols',  # enable {% break %}, {% continue %}
            ]
        )
        for name, factory in self._filter_factories.items():
            self.filters[name] = factory(self._builder.env)


class Phase(Enum):
    Parsing = 'parsing'
    Parsed = 'parsed'
    Resolving = 'resolving'

    @classmethod
    def default(cls) -> Phase:
        return cls.Parsing

    @classmethod
    def option_spec(cls, arg):
        choice = directives.choice(arg, [x.value for x in cls])
        return cls[choice.title()]


@dataclasses.dataclass(frozen=True)
class Template(object):
    text: str
    phase: Phase
    debug: bool

    @classmethod
    def default(cls) -> Template:
        return Template('THIS IS A DEFAULT TEMPLATE', Phase.default(), False)

    def render(self, ctx: dict[str, Any]) -> str:
        return JinjaEnv().from_string(self.text).render(ctx)


type Parser = Callable[[str], list[nodes.Node]]


def render(
    parser: Parser, tmpl: Template, data: Data, extractx: dict[str, Any]
) -> list[nodes.Node]:
    ctx = data.ascontext()
    ctx.update(**extractx)
    text = tmpl.render(ctx)

    ns = parser(text)

    if tmpl.debug:
        nsstr = '\n'.join(n.pformat() for n in ns)
        ns += report('data', pformat(data))
        ns += report('template', pformat(tmpl))
        ns += report('rendered node', nsstr)

    return ns


def report(title: str, content: str | None) -> nodes.system_message:
    sm = nodes.system_message(title + ':', type='WARNING', level=2, source='')
    if content:
        sm += nodes.literal_block(content, content)
    return sm
