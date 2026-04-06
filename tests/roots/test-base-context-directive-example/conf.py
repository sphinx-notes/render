from sphinx.application import Sphinx
from sphinxnotes.render import ParsedData, BaseContextDirective, Template, Phase


class MimiDirective(BaseContextDirective):
    def current_context(self):
        return ParsedData(
            name='mimi',
            attrs={'color': 'black and brown'},
            content='I like fish!',
        )

    def current_template(self):
        return Template(
            'Hi human! I am a cat named {{ name }}, I have {{ color }} fur.\n\n'
            '{{ content }}.',
            phase=Phase.Parsing,
        )


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('mimi', MimiDirective)
