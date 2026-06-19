from sphinxnotes.render import filter
from sphinx.environment import BuildEnvironment


# fmt: off
# [literalinclude catify-start]
@filter('catify')
def catify(value: str) -> str:
    """Speak in a cat-like tone"""
    return value + ', meow~'
# [literalinclude catify-end]
# fmt: on


# fmt: off
# [literalinclude author-start]
@filter('format_author', pass_build_env=True)
def format_author(env: BuildEnvironment, value: str) -> str:
    """Replace 'author' in value with the Sphinx document author"""
    return value.replace('author', env.config.author)
# [literalinclude author-end]
# fmt: on


# [literalinclude end]
extensions = ['sphinxnotes.render.ext']


def setup(app): ...
