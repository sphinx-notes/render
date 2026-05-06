from types import SimpleNamespace

from sphinxnotes.render.extractx import (
    ExtraContext,
    ExtraContextRequest,
    _REGISTRY,
    build_load_extra,
)
from sphinxnotes.render.template import Template
from sphinxnotes.render.ctxnodes import pending_node


class CountingExtraContext(ExtraContext):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return self.calls


def test_extra_context_loader_does_not_cache_values():
    name = 'test_no_cache'
    ctx = CountingExtraContext()
    _REGISTRY.register(name, ctx)

    try:
        node = pending_node({}, Template(''))
        host = SimpleNamespace(env=SimpleNamespace())
        request = ExtraContextRequest(Template('').phase, node, host.env, host)
        load_extra = build_load_extra(request)

        assert load_extra(name) == 1
        assert load_extra(name) == 2
    finally:
        _REGISTRY.ctxs.pop(name, None)
