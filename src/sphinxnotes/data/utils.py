from typing import TypeVar, Generic, get_args
import dataclasses

from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser
from docutils.utils import new_document

from dacite import from_dict


def parse_text_to_nodes(text: str) -> list[nodes.Node]:
    """
    Utility for parsing standard reStructuredText (without Sphinx stuffs) to nodes.
    Used when there is not a Sphinx parser available.
    """
    # TODO: markdown support
    document = new_document('<string>', settings=get_default_settings(Parser))  # type: ignore
    Parser().parse(text, document)
    return document.children


_Element = TypeVar('_Element', bound=nodes.Element)


def find_parent(node: nodes.Element | None, typ: type[_Element]) -> _Element | None:
    if node is None or isinstance(node, typ):
        return node
    return find_parent(node.parent, typ)


def find_current_section(node: nodes.Element | None) -> nodes.section | None:
    return find_parent(node, nodes.section)


def find_current_document(node: nodes.Element | None) -> nodes.document | None:
    return find_parent(node, nodes.document)


DataT = TypeVar('DataT')


class TempData(Generic[DataT]):
    """A helper class for storing/accessing dataclasses to/from a docutils node."""

    KEY = 'sphinxnotes-data'

    @classmethod
    def _get_data_type(cls) -> type[DataT]:
        """
        Dynamically extract the actual type of DataT from the class definition.

        Example: For `class MyHelper(TempData[MyStruct])`, this returns `MyStruct`.
        """
        # Access the original base classes (including generic type args)
        # This attribute is available in Python 3.7+
        for base in getattr(cls, '__orig_bases__', []):
            origin = getattr(base, '__origin__', None)
            # Check if this base is the TempData class itself
            if origin is TempData:
                args = get_args(base)
                if args:
                    # Return the first generic argument, which corresponds to DataT
                    return args[0]
        raise TypeError(
            f'Cannot infer DataT from {cls.__name__}. '
            'Ensure you are subclassing TempData[MyType] rather than using it directly.'
        )

    @classmethod
    def _get_type_name(cls) -> str:
        return cls._get_data_type().__name__

    @classmethod
    def set(cls, node: nodes.Element, data: DataT) -> None:
        tempdata = node.setdefault(cls.KEY, {})
        assert dataclasses.is_dataclass(data)
        tempdata[cls._get_type_name()] = dataclasses.asdict(data)  # type: ignore

    @classmethod
    def get(cls, node: nodes.Element) -> DataT | None:
        if (tempdata := node.get(cls.KEY)) is None:
            return None
        if (data := tempdata.get(cls._get_type_name())) is None:
            return None
        return from_dict(data_class=cls._get_data_type(), data=data)
