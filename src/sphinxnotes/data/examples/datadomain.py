"""
sphinxnotes.data.examples.datadomain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Allow user define, validate, and render data in pure markup and Jinja template.

All directives and roles are added to a domain to prevent naming conflicts.

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, cast

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective, CustomReSTDispatcher
from sphinx.domains import Domain

from ..data import RawData, Field, Schema
from ..render import Phase, Template, BaseDataDefineDirective, BaseDataDefineRole
from ..utils.freestyle import FreeStyleDirective, FreeStyleOptionSpec

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from types import ModuleType
    from docutils.utils import Reporter
    from sphinx.util.typing import RoleFunction


# Keys of env.temp_data.
TEMPLATE_KEY = 'sphinxnotes-data:template'
SCHEMA_KEY = 'sphinxnotes-data:schema'


def phase_option_spec(arg):
    choice = directives.choice(arg, [x.value for x in Phase])
    return Phase[choice.title()]


class TemplateDefineDirective(SphinxDirective):
    option_spec = {
        'on': phase_option_spec,
        'debug': directives.flag,
    }
    has_content = True

    def run(self) -> list[nodes.Node]:
        self.env.temp_data[TEMPLATE_KEY] = Template(
            '\n'.join(self.content),
            phase=self.options.get('on', Phase.default()),
            debug='debug' in self.options,
        )

        return []

    @staticmethod
    def directive_preset() -> Template:
        return Template("""
.. note::

   This is a default template for rendering the data your deinfed.
   Please create your own template using the :rst:dir:`data:tmpl` directive.

:Name: ``{{ name or 'None' }}``
{% for k, v in attrs.items() %}
:{{ k }}: ``{{ v or 'None' }}``
{%- endfor %}
:content:
    ::

        {{ content or 'None' }}""")

    @staticmethod
    def role_preset() -> Template:
        return Template("""``{{ content or 'None' }}``
:abbr:`ⁱⁿᶠᵒ (This is a default template for rendering the data your deinfed
Please create your own template using the data.tmpl directive.)`""")


class SchemaDefineDirective(FreeStyleDirective):
    optional_arguments = 1
    option_spec = FreeStyleOptionSpec()
    has_content = True

    def run(self) -> list[nodes.Node]:
        name = Field.from_dsl(self.arguments[0]) if self.arguments else None
        attrs = {}
        for k, v in self.options.items():
            attrs[k] = Field.from_dsl(v)
        content = Field.from_dsl(self.content[0]) if self.content else None

        self.env.temp_data[SCHEMA_KEY] = Schema(name, attrs, content)

        return []

    @staticmethod
    def directive_preset() -> Schema:
        return Schema(name=Field(), attrs=Field(), content=Field())

    @staticmethod
    def role_preset() -> Schema:
        return Schema(name=Field(), attrs={}, content=Field())


class FreeDataDefineDirective(BaseDataDefineDirective, FreeStyleDirective):
    optional_arguments = 1
    has_content = True

    @override
    def current_schema(self) -> Schema:
        schema = self.env.temp_data.get(
            SCHEMA_KEY, SchemaDefineDirective.directive_preset()
        )
        return cast(Schema, schema)

    @override
    def current_template(self) -> Template:
        tmpl = self.env.temp_data.get(
            TEMPLATE_KEY, TemplateDefineDirective.directive_preset()
        )
        return cast(Template, tmpl)


class FreeDataDefineRole(BaseDataDefineRole):
    def __init__(self, orig_name: str) -> None:
        self.orig_name = orig_name

    @override
    def current_data(self) -> RawData:
        _, _, name = self.orig_name.partition('+')
        return RawData(name, {}, self.text)

    @override
    def current_schema(self) -> Schema:
        schema = self.env.temp_data.get(SCHEMA_KEY, SchemaDefineDirective.role_preset())
        return cast(Schema, schema)

    @override
    def current_template(self) -> Template:
        tmpl = self.env.temp_data.get(
            TEMPLATE_KEY, TemplateDefineDirective.role_preset()
        )
        return cast(Template, tmpl)


class DataDefineRoleDispatcher(CustomReSTDispatcher):
    """Custom dispatcher for data define role.

    This enables :data:def+***:/def+***: roles on parsing reST document.

    .. seealso:: :cls:`sphinx.ext.intersphinx.IntersphinxDispatcher`.
    """

    @override
    def role(
        self,
        role_name: str,
        language_module: ModuleType,
        lineno: int,
        reporter: Reporter,
    ) -> tuple[RoleFunction, list[nodes.system_message]]:
        if len(role_name) > 4 and role_name.startswith(('data:def+', 'def+')):
            return FreeDataDefineRole(role_name), []
        else:
            return super().role(role_name, language_module, lineno, reporter)


class DataDomain(Domain):
    name = 'data'
    label = 'Data'
    object_types = {}
    directives = {
        'template': TemplateDefineDirective,
        'tmpl': TemplateDefineDirective,
        'schema': SchemaDefineDirective,
        'def': FreeDataDefineDirective,
        'define': FreeDataDefineDirective,
    }
    roles = {
        'def': FreeDataDefineRole(''),
    }
    indices = []
    initial_data = {}


def _install_dispatcher(app: Sphinx, docname: str, source: list[str]) -> None:
    """Enable IntersphinxDispatcher.

    .. note:: The installed dispatcher will be uninstalled on disabling sphinx_domain
              automatically.
    """
    DataDefineRoleDispatcher().enable()


def setup(app: Sphinx):
    app.add_domain(DataDomain)
    app.connect('source-read', _install_dispatcher)
