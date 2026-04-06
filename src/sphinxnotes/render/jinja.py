"""
sphinxnotes.jinja
~~~~~~~~~~~~~~~~~

Rendering Jinja2 template to markup text.

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from dataclasses import dataclass
from pprint import pformat
from typing import TYPE_CHECKING, Callable, ClassVar, override

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import StrictUndefined, DebugUndefined

from .data import ParsedData
from .utils import Report

if TYPE_CHECKING:
    from typing import Any
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


@dataclass
class TemplateRenderer:
    text: str

    def render(
        self,
        data: ParsedData | dict[str, Any],
        extra: dict[str, Any] = {},
        debug: Report | None = None,
    ) -> str:
        if debug:
            debug.text('Starting Jinja template rendering...')

            debug.text('Data:')
            debug.code(pformat(data), lang='python')
            debug.text('Available extra context (just keys):')
            debug.code(pformat(list(extra.keys())), lang='python')

        # Convert data to context dict.
        if isinstance(data, ParsedData):
            ctx = data.asdict()
        elif isinstance(data, dict):
            ctx = data.copy()

        # Inject load_extra() function for accessing extra context.
        # TODO: move to extractx.py
        def load_extra(name: str):
            if name not in extra:
                raise ValueError(
                    f'Extra context "{name}" is not available. '
                    f'Available: {list(extra.keys())}'
                )
            return extra[name]

        ctx['load_extra'] = load_extra

        text = self._render(ctx, debug=debug is not None)

        return text

    def _render(self, ctx: dict[str, Any], debug: bool = False) -> str:
        extensions = [
            'jinja2.ext.loopcontrols',  # enable {% break %}, {% continue %}
            'jinja2.ext.do',  # enable {% do ... %}
        ]
        if debug:
            extensions.append('jinja2.ext.debug')

        env = _JinjaEnv(
            undefined=DebugUndefined if debug else StrictUndefined,
            extensions=extensions,
        )
        # TODO: cache jinja env

        return env.from_string(self.text).render(ctx)

    def _report_self(self, reporter: Report) -> None:
        reporter.text('Template:')
        reporter.code(self.text, lang='jinja')


class _JinjaEnv(SandboxedEnvironment):
    _env: ClassVar[BuildEnvironment]
    _filter_factories: ClassVar[dict[str, Callable[[BuildEnvironment], Callable]]] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, factory in self._filter_factories.items():
            self.filters[name] = factory(self._env)

    @classmethod
    def on_builder_inited(cls, app: Sphinx):
        cls._env = app.env

    @classmethod
    def add_filter(cls, name: str, factory: Callable[[BuildEnvironment], Callable]):
        cls._filter_factories[name] = factory

    @override
    def is_safe_attribute(self, obj, attr, value=None):
        """
        The sandboxed environment will call this method to check if the
        attribute of an object is safe to access. Per default all attributes
        starting with an underscore are considered private as well as the
        special attributes of internal python objects as returned by the
        is_internal_attribute() function.

        .. seealso:: :class:`..utils.ctxproxy.Proxy`
        """
        return super().is_safe_attribute(obj, attr, value)


def filter(name: str):
    """Decorator for adding a filter to the Jinja environment.

    Usage::

        @filter('my_filter')
        def my_filter(env: BuildEnvironment):
            def _filter(value):
                return value.upper()
            return _filter
    """

    def decorator(ff):
        _JinjaEnv.add_filter(name, ff)
        return ff

    return decorator


def setup(app: Sphinx):
    app.connect('builder-inited', _JinjaEnv.on_builder_inited)
