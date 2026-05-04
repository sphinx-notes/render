import pickle

from sphinxnotes.render.ctx import UnresolvedContext
from sphinxnotes.render.ctxnodes import pending_node
from sphinxnotes.render.data import RawData, Schema
from sphinxnotes.render.sources import UnparsedData
from sphinxnotes.render.template import Phase, Template
from sphinxnotes.render.utils import Report, Unpicklable


class UnpicklableUnresolvedContext(UnresolvedContext, Unpicklable):
    def resolve(self):
        return {}

    def __hash__(self) -> int:
        return 0


def test_schema_and_unparsed_data_are_picklable():
    schema = Schema.from_dsl(
        name='str',
        attrs={'age': 'int', 'tags': 'words of str'},
        content='str',
    )
    pending = UnparsedData(
        RawData('mimi', {'age': '2', 'tags': 'cat cute'}, 'hello'),
        schema,
    )

    restored = pickle.loads(pickle.dumps(pending))

    assert restored.resolve().name == 'mimi'
    assert restored.resolve().attrs == {'age': 2, 'tags': ['cat', 'cute']}
    assert restored.resolve().content == 'hello'


def test_pending_node_reports_unpicklable_unresolved_context_for_later_phase():
    node = pending_node(
        UnpicklableUnresolvedContext(),
        Template('ignored', phase=Phase.Parsed),
    )

    node.rendered = False
    node.render(host=None)

    reports = [child for child in node.children if isinstance(child, Report)]

    assert len(reports) == 1
    assert reports[0].is_error()
    assert 'UnresolvedContext' in reports[0].astext()
    assert 'picklable' in reports[0].astext()


def test_pending_node_allows_unpicklable_unresolved_context_for_parsing_phase():
    node = pending_node(
        UnpicklableUnresolvedContext(),
        Template('ignored', phase=Phase.Parsing),
    )

    assert isinstance(node.ctx, UnpicklableUnresolvedContext)
