import pickle

from sphinxnotes.render.data import RawData, Schema
from sphinxnotes.render.sources import UnparsedData


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
