# [literalinclude start]
from sphinxnotes.render import (
    extra_context,
    ExtraContext,
    ExtraContextRequest,
)


@extra_context('all_docs')
class AllDocsExtraContext(ExtraContext):
    def generate(self, req: ExtraContextRequest, *args, **kwargs):
        count = args[0] if args else kwargs.get('count', 5)
        return sorted(req.env.all_docs.keys())[:count]


# [literalinclude end]

extensions = ['sphinxnotes.render.ext']


def setup(app): ...
