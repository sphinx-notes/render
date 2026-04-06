# [literalinclude start]
from os import path
import json

from sphinx.environment import BuildEnvironment
from sphinxnotes.render import (
    extra_context,
    GlobalExtraContext,
)

@extra_context('cat')
class CatExtraContext(GlobalExtraContext):
    def generate(self, env: BuildEnvironment):
        with open(path.join(path.dirname(__file__), 'cat.json')) as f:
            return json.loads(f.read())
# [literalinclude end]


extensions = ['sphinxnotes.render.ext']


def setup(app): ...
