from sphinx.application import Sphinx
from sphinxnotes.render import ParsedData, BaseContextDirective, Template, Phase

class MyDirective(BaseContextDirective):
    def current_context(self):
        return ParsedData('Shengyu Zhang', {}, None)

    def current_template(self):
        return Template('My name is {{ name }}', phase=Phase.Parsing)


def setup(app: Sphinx):
    app.setup_extension('sphinxnotes.render')
    app.add_directive('me', MyDirective)
