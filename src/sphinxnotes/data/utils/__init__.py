from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, cast

from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser
from docutils.parsers.rst.states import Struct
from docutils.utils import new_document
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Literal, Iterable
    from sphinx.util.docutils import SphinxRole

logger = logging.getLogger(__name__)


def parse_text_to_nodes(text: str) -> list[nodes.Node]:
    """
    Utility for parsing standard reStructuredText (without Sphinx stuffs) to nodes.
    Used when there is not a SphinxDirective/SphinxRole available.
    """
    # TODO: markdown support
    document = new_document('<string>', settings=get_default_settings(Parser))  # type: ignore
    Parser().parse(text, document)
    return document.children


def role_parse_text_to_nodes(self: SphinxRole, text: str) -> list[nodes.Node]:
    """
    Utility for parsing reStructuredText (without Sphinx stuffs) to nodes in
    SphinxRole Context.
    """
    memo = Struct(
        document=self.inliner.document,
        reporter=self.inliner.reporter,
        language=self.inliner.language,
    )
    ns, msgs = self.inliner.parse(text, self.lineno, memo, self.inliner.parent)
    return ns + msgs


_Node = TypeVar('_Node', bound=nodes.Node)


def find_parent(node: nodes.Node | None, typ: type[_Node]) -> _Node | None:
    if node is None or isinstance(node, typ):
        return node
    return find_parent(node.parent, typ)


def find_current_section(node: nodes.Node | None) -> nodes.section | None:
    return find_parent(node, nodes.section)


def find_current_document(node: nodes.Node | None) -> nodes.document | None:
    return find_parent(node, nodes.document)


def find_first_child(node: nodes.Element, cls: type[_Node]) -> _Node | None:
    if (index := node.first_child_matching_class(cls)) is None:
        return None
    return cast(_Node, node[index])


def find_titular_node_upward(node: nodes.Element | None) -> nodes.Element | None:
    if node is None:
        return None
    if isinstance(node, (nodes.section, nodes.sidebar)):
        if title := find_first_child(node, nodes.title):
            return title
    if isinstance(node, nodes.definition_list_item):
        if term := find_first_child(node, nodes.term):
            return term
    if isinstance(node, nodes.field):
        if field := find_first_child(node, nodes.field_name):
            return field
    if isinstance(node, nodes.list_item):
        if para := find_first_child(node, nodes.paragraph):
            return para
    return find_titular_node_upward(node.parent)


class Reporter(nodes.system_message):
    def __init__(
        self,
        title: str,
        level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'DEBUG',
    ) -> None:
        super().__init__(title + ':', type=level, level=2, source='')

    def report(self, node: nodes.Node) -> None:
        self += node
        # TODO: print log here

    def text(self, text: str) -> None:
        self.report(nodes.paragraph(text, text))

    def code(self, code: str, lang: str | None = None) -> None:
        blk = nodes.literal_block(code, code)
        if lang:
            blk['language'] = lang
        self.report(blk)

    def list(self, lines: Iterable[str]) -> None:
        bullet_list = nodes.bullet_list(bullet='*')
        
        for line in lines:
            list_item = nodes.list_item()
            para = nodes.paragraph()
            para += nodes.Text(line)
            list_item += para
            bullet_list += list_item
            
        self.report(bullet_list)
