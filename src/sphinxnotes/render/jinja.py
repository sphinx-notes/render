"""
sphinxnotes.jinja
~~~~~~~~~~~~~~~~~

Rendering Jinja2 template to markup text.

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ClassVar, override

from jinja2.sandbox import SandboxedEnvironment
from jinja2 import StrictUndefined, DebugUndefined

from .data import ParsedData

if TYPE_CHECKING:
    from typing import Any
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from .ctx import ResolvedContext


class JinjaRegistry:
    """Registry for customizing the Jinja2 environment.

    Provides methods to add custom filters and extensions to the Jinja2
    rendering environment used by this extension.
    """

    _filters: dict[str, Callable[[BuildEnvironment], Callable]]
    _extensions: list[str]

    def __init__(self) -> None:
        self._filters = {}
        self._extensions = []

    def add_filter(
        self, name: str, factory: Callable[[BuildEnvironment], Callable]
    ) -> None:
        """Register a filter factory.

        :param name: The filter name, used in Jinja templates as ``{{ value|name }}``
        :param factory: A callable that takes a :py:class:`~sphinx.environment.BuildEnvironment`
                        and returns a filter callable

        .. note:: Using the :py:deco:`filter` decorator is recommended for most cases.

        """
        if name in self._filters:
            raise ValueError(f'Jinja filter "{name}" already registered')
        self._filters[name] = factory

    def add_extension(self, extension: str) -> None:
        """Add a Jinja2 extension.

        See `Jinja2 Extensions <https://jinja.palletsprojects.com/en/stable/extensions/>`_
        for available builtin extensions.

        :param extension: The extension module path, e.g. ``'jinja2.ext.i18n'``
        """
        if extension not in self._extensions:
            self._extensions.append(extension)


REGISTRY = JinjaRegistry()
"""The global registry for Jinja2 filter factories."""


@dataclass
class TemplateRenderer:
    text: str

    def render(
        self,
        data: ResolvedContext,
        globals: dict[str, Any] | None = None,
        debug: bool = False,
    ) -> str:
        # Convert data to context dict.
        if isinstance(data, ParsedData):
            ctx = data.asdict()
        elif isinstance(data, dict):
            ctx = data.copy()

        # Inject globals.
        if globals:
            ctx.update(globals)

        return self._render(ctx, debug=debug)

    def _render(self, ctx: dict[str, Any], debug: bool = False) -> str:
        extensions = list(REGISTRY._extensions)
        if debug:
            extensions.append('jinja2.ext.debug')

        env = _JinjaEnv(
            undefined=DebugUndefined if debug else StrictUndefined,
            extensions=extensions,
        )
        # TODO: cache jinja env

        return env.from_string(self.text).render(ctx)


class _JinjaEnv(SandboxedEnvironment):
    _env: ClassVar[BuildEnvironment]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, factory in REGISTRY._filters.items():
            self.filters[name] = factory(self._env)

    @classmethod
    def on_builder_inited(cls, app: Sphinx):
        cls._env = app.env

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
        REGISTRY.add_filter(name, ff)
        return ff

    return decorator


def setup(app: Sphinx):
    app.connect('builder-inited', _JinjaEnv.on_builder_inited)

    REGISTRY.add_extension('jinja2.ext.loopcontrols')
    REGISTRY.add_extension('jinja2.ext.do')
