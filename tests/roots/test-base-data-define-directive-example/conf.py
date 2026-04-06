from datetime import datetime

from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinxnotes.render import (
    BaseDataDefineDirective,
    Schema,
    Field,
    Template,
)


class CatDirective(BaseDataDefineDirective):
    required_arguments = 1
    option_spec = {
        'color': directives.unchanged,
        'birth': directives.unchanged,
    }
    has_content = True

    def current_schema(self):
        return Schema(
            name=Field.from_dsl('str'),
            attrs={
                'color': Field.from_dsl('list of str'),
                'birth': Field.from_dsl('int'),
            },
            content=Field.from_dsl('str'),
        )

    def current_template(self):
        year = datetime.now().year
        return Template(
            'Hi human! I am a cat named {{ name }}, I have {{ "and".join(color) }} fur.\n'
            f'I am {{{{ {year} - birth }}}} years old.\n\n'
            '{{ content }}.'
        )


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('cat2', CatDirective)
