"""
sphinxnotes.render.ext.derive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import Schema, Template, Phase, StrictDataDefineDirective

from schema import Schema as DictSchema, SchemaError as DictSchemaError, Optional, Or
from sphinx.errors import ConfigError

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config


DATA_DEFINE_DIRECTIVE = DictSchema(
    {
        'schema': {
            Optional('name', default='str, required, uniq, ref'): Or(str, type(None)),
            Optional('attrs', default={}): {str: str},
            Optional('content', default='str'): Or(str, type(None)),
        },
        'template': {
            Optional('on', default='parsing'): Or('parsing', 'parsed', 'resolving'),
            'text': str,
            Optional('debug', default=False): bool,
        },
    }
)


def _validate_directive_define(d: dict, config: Config) -> tuple[Schema, Template]:
    validated = DATA_DEFINE_DIRECTIVE.validate(d)

    schemadef = validated['schema']
    schema = Schema.from_dsl(
        schemadef['name'], schemadef['attrs'], schemadef['content']
    )

    tmpldef = validated['template']
    phase = Phase[tmpldef['on'].title()]
    template = Template(text=tmpldef['text'], phase=phase, debug=tmpldef['debug'])

    return schema, template


def _config_inited(app: Sphinx, config: Config) -> None:
    for name, objdef in app.config.data_define_directives.items():
        try:
            schema, tmpl = _validate_directive_define(objdef, config)
        except (DictSchemaError, ValueError) as e:
            raise ConfigError(
                f'Validating data_define_directives[{repr(name)}]: {e}'
            ) from e

        directive_cls = StrictDataDefineDirective.derive(name, schema, tmpl)
        app.add_directive(name, directive_cls)


def setup(app: Sphinx) -> None:
    app.add_config_value('data_define_directives', {}, 'env', types=dict)
    app.connect('config-inited', _config_inited)
