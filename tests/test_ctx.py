import pickle
from unittest.mock import MagicMock

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

    mock_env = MagicMock()
    assert restored.resolve(mock_env).name == 'mimi'
    assert restored.resolve(mock_env).attrs == {'age': 2, 'tags': ['cat', 'cute']}
    assert restored.resolve(mock_env).content == 'hello'
