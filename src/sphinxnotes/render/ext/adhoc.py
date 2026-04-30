"""
sphinxnotes.render.ext.adhoc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

Provides directives and roles for temporarily rendering data within a document.

"""

from __future__ import annotations
from typing import TYPE_CHECKING, override, cast

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective, CustomReSTDispatcher

from .. import (
    RawData,
    Field,
    Schema,
    Phase,
    Template,
    BaseContextDirective,
    BaseDataDefineDirective,
    BaseDataDefineRole,
)
from ..utils.freestyle import FreeStyleDirective

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from types import ModuleType
    from docutils.utils import Reporter
    from sphinx.util.typing import RoleFunction
    from .. import UnresolvedContext, ResolvedContext


# Keys of env.temp_data.
TEMPLATE_KEY = 'sphinxnotes.render.ext:template'
SCHEMA_KEY = 'sphinxnotes.render.ext:schema'


def phase_option_spec(arg):
    choice = directives.choice(arg, [x.value for x in Phase])
    return Phase[choice.title()]


class TemplateDefineDirective(SphinxDirective):
    option_spec = {
        'on': phase_option_spec,
        'debug': directives.flag,
        'extra': directives.unchanged,
    }
    has_content = True

    @override
    def run(self) -> list[nodes.Node]:
        extra = self.options.get('extra', '')

        self.env.temp_data[TEMPLATE_KEY] = Template(
            '\n'.join(self.content),
            phase=self.options.get('on', Phase.default()),
            debug='debug' in self.options,
            extra=extra.split() if extra else [],
        )

        return []

    @staticmethod
    def directive_preset() -> Template:
        return Template("""
.. code:: py

   {
      'name': '{{ name }}',
      'attrs': {{ attrs }},
      'content': '{{ content }}'

      # Lifted attrs
      {% for k, v in attrs.items() -%}
      '{{ k }}': '{{ v }}',
      {%- endfor %}
   }""")

    @staticmethod
    def role_preset() -> Template:
        return Template("""``{{ content or 'None' }}``""")


class SchemaDefineDirective(FreeStyleDirective):
    optional_arguments = 1
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


class DataRenderDirective(BaseContextDirective):
    option_spec = {
        'on': phase_option_spec,
        'debug': directives.flag,
        'extra': directives.unchanged,
    }
    has_content = True

    @override
    def current_context(self) -> UnresolvedContext | ResolvedContext:
        return {}

    @override
    def current_template(self) -> Template:
        extra_str = self.options.get('extra', '')
        extra_list = extra_str.split() if extra_str else []

        return Template(
            '\n'.join(self.content),
            phase=self.options.get('on', Phase.default()),
            debug='debug' in self.options,
            extra=extra_list,
        )


class FreeDataDefineRole(BaseDataDefineRole):
    def __init__(self, orig_name: str) -> None:
        self.orig_name = orig_name

    @override
    def current_raw_data(self) -> RawData:
        data = super().current_raw_data()
        _, _, data.name = self.orig_name.partition('+')
        return data

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


class FreeDataDefineRoleDispatcher(CustomReSTDispatcher):
    """Custom dispatcher for data define role.

    This enables :data:def+***:/def+***: roles on parsing reST document.

    .. seealso:: :class:`sphinx.ext.intersphinx.IntersphinxDispatcher`.
    """

    @override
    def role(
        self,
        role_name: str,
        language_module: ModuleType,
        lineno: int,
        reporter: Reporter,
    ) -> tuple[RoleFunction, list[nodes.system_message]]:
        if len(role_name) > 4 and role_name.startswith('data:define+'):
            return FreeDataDefineRole(role_name), []
        else:
            return super().role(role_name, language_module, lineno, reporter)

    def install(self, app: Sphinx, docname: str, source: list[str]) -> None:
        """Enable role ispatcher.

        .. note:: The installed dispatcher will be uninstalled on disabling sphinx_domain
                  automatically.
        """
        self.enable()


def setup(app: Sphinx) -> None:
    app.add_directive('data.define', FreeDataDefineDirective)
    app.add_directive('data.template', TemplateDefineDirective)
    app.add_directive('data.schema', SchemaDefineDirective)
    app.add_directive('data.render', DataRenderDirective)

    app.add_role('data.define', FreeDataDefineRole)

    app.connect('source-read', FreeDataDefineRoleDispatcher().install)
