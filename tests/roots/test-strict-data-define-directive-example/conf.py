from datetime import datetime

from sphinx.application import Sphinx
from sphinxnotes.render import (
    StrictDataDefineDirective,
    Schema,
    Field,
    Template,
)

schema = Schema(
    name=Field.from_dsl('str'),
    attrs={
        'color': Field.from_dsl('list of str'),
        'birth': Field.from_dsl('int'),
    },
    content=Field.from_dsl('str'),
)

template = Template(
    'Hi human! I am a cat named {{ name }}, I have {{ "and".join(color) }} fur.\n'
    f'I am {{{{ {datetime.now().year} - birth }}}} years old.\n\n'
    '{{ content }}.'
)

CatDirective = StrictDataDefineDirective.derive('cat', schema, template)


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('cat3', CatDirective)
