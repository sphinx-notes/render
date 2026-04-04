from sphinx.application import Sphinx
from sphinxnotes.render import (
    extra_context,
    ParsingPhaseExtraContext,
    GlobalExtraContext,
    BaseContextDirective,
    Template,
)


@extra_context('custom_parsing')
class CustomParsingExtraContext(ParsingPhaseExtraContext):
    def generate(self, directive):
        return {'custom_value': 'parsing_test'}


@extra_context('custom_global')
class CustomGlobalExtraContext(GlobalExtraContext):
    def generate(self, env):
        return {'custom_value': 'global_test'}


class CustomExtraContextDirective(BaseContextDirective):
    def current_context(self):
        return {}

    def current_template(self):
        return Template(
            """
{% set _parsing = load('custom_parsing') %}
{% set _global = load('custom_global') %}
Parsing: {{ _parsing.custom_value }}
Global: {{ _global.custom_value }}
""",
            extra=['custom_parsing', 'custom_global'],
        )


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('custom-extra', CustomExtraContextDirective)
