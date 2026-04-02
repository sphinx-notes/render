from sphinx.application import Sphinx
from sphinxnotes.render import StrictDataDefineDirective, Schema, Template


CardDirective = StrictDataDefineDirective.derive(
    'card',
    Schema.from_dsl(
        name='str, required',
        attrs={
            'tags': 'list of str',
            'featured': 'bool',
        },
        content='str',
    ),
    Template(
        '\n'.join(
            [
                '.. rubric:: {{ name }}',
                '{% if featured %}',
                '.. important:: Featured entry',
                '{% endif %}',
                '',
                '{% if tags %}',
                ':Tags: {{ tags | join(", ") }}',
                '{% endif %}',
                '',
                '{{ content }}',
            ]
        )
    ),
)


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('card', CardDirective)
