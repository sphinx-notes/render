from types import SimpleNamespace

from sphinxnotes.render.extractx import (
    ExtraContext,
    ExtraContextRequest,
    REGISTRY,
    extra_context_loader,
)
from sphinxnotes.render.template import Template
from sphinxnotes.render.ctxnodes import pending_node


class CountingExtraContext(ExtraContext):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, req, *args, **kwargs):
        self.calls += 1
        return self.calls


def test_extra_context_loader_does_not_cache_values():
    name = 'test_no_cache'
    ctx = CountingExtraContext()
    REGISTRY.add(name, ctx)

    try:
        node = pending_node({}, Template(''))
        host = SimpleNamespace(env=SimpleNamespace())
        req = ExtraContextRequest(Template('').phase, node, host.env, host)
        load_extra = extra_context_loader(req)

        assert load_extra(name) == 1
        assert load_extra(name) == 2
    finally:
        REGISTRY._ctxs.pop(name, None)


class ParamExtraContext(ExtraContext):
    def generate(self, req, *args, **kwargs):
        return {'args': args, 'kwargs': kwargs}


def test_extra_context_loader_passes_parameters():
    name = 'test_params'
    REGISTRY.add(name, ParamExtraContext())

    try:
        node = pending_node({}, Template(''))
        host = SimpleNamespace(env=SimpleNamespace())
        req = ExtraContextRequest(Template('').phase, node, host.env, host)
        load_extra = extra_context_loader(req)

        result = load_extra(name, 10, limit=20)
        assert result == {'args': (10,), 'kwargs': {'limit': 20}}
    finally:
        REGISTRY._ctxs.pop(name, None)
