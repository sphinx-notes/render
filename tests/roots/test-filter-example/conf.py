from sphinxnotes.render import filter
from sphinx.environment import BuildEnvironment


# [literalinclude start]
@filter('catify')
def catify(_: BuildEnvironment):
    """Speak in a cat-like tone"""

    def _filter(value: str) -> str:
        return value + ', meow~'

    return _filter


# [literalinclude end]


extensions = ['sphinxnotes.render.ext']


def setup(app): ...
