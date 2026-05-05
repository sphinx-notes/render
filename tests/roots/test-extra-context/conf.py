# [literalinclude start]
from os import path
import json

from sphinxnotes.render import (
    extra_context,
    ExtraContext,
    ExtraContextRequest,
)


@extra_context('cat')
class CatExtraContext(ExtraContext):
    def generate(self, request: ExtraContextRequest):
        with open(path.join(path.dirname(__file__), 'cat.json')) as f:
            return json.loads(f.read())


# [literalinclude end]


extensions = ['sphinxnotes.render.ext']


def setup(app): ...
