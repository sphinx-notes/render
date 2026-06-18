from __future__ import annotations
from dataclasses import dataclass
import sys
from typing import TYPE_CHECKING, TypeVar, cast
import traceback

from docutils import nodes
from docutils.frontend import get_default_settings
from docutils.parsers.rst import Parser
from docutils.parsers.rst.states import Struct, Inliner as RstInliner
from docutils.utils import new_document
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Literal, Iterable, Callable
    from sphinx.util.docutils import SphinxRole

logger = logging.getLogger(__name__)


def parse_text_to_nodes(text: str) -> list[nodes.Node]:
    """
    Utility for parsing standard reStructuredText (without Sphinx-specific features) to nodes.
    Used when there is not a SphinxDirective/SphinxRole available.
    """
    # TODO: markdown support
    document = new_document('<string>', settings=get_default_settings(Parser))  # type: ignore
    Parser().parse(text, document)
    return document.children


def role_parse_text_to_nodes(self: SphinxRole, text: str) -> list[nodes.Node]:
    """
    Utility for parsing reStructuredText (without Sphinx-specific features) to nodes in
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


def find_nearest_block_element(node: nodes.Node | None) -> nodes.Element | None:
    """
    Finds the nearest ancestor that is suitable for block-level placement.
    Typically a Body element (paragraph, table, list) or Structural element (section).
    """
    while node:
        if isinstance(node, (nodes.Body, nodes.Structural, nodes.document)):
            return node
        node = node.parent
    return None


class Report(nodes.system_message):
    type Level = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']

    title: str

    def __init__(
        self, title: str, level: Level = 'DEBUG', *children, **attributes
    ) -> None:
        super().__init__(title + ':', type=level, level=2, *children, **attributes)
        self.title = title

    @property
    def level(self) -> Level:
        return self['type']

    @level.setter
    def level(self, level: Level):
        self['type'] = level

    def empty(self) -> bool:
        # title is the only children
        return len(self.children) <= 1

    def node(self, node: nodes.Node) -> None:
        self += node
        self.log(f'report: {node.astext()}')

    def log(self, msg: str) -> None:
        if self['type'] in 'ERROR':
            logger.error(msg)
        elif self['type'] in 'WARNING':
            logger.warning(msg)

    def text(self, text: str) -> None:
        self.node(nodes.paragraph(text, text))

    def code(
        self, code: str, lang: str | None = None, caption: str | None = None
    ) -> None:
        blk = nodes.literal_block(code, code)
        if lang:
            blk['language'] = lang
        if caption:
            # See also: :meth:`sphinx.directives.code.container_wrapper`.
            container = nodes.container(
                '', literal_block=True, classes=['literal-block-wrapper']
            )
            container += nodes.caption(caption, '', nodes.Text(caption))
            container += blk
            self.node(container)
        else:
            self.node(blk)

    def list(self, lines: Iterable[str]) -> None:
        bullet_list = nodes.bullet_list(bullet='*')

        for line in lines:
            list_item = nodes.list_item()
            para = nodes.paragraph()
            para += nodes.Text(line)
            list_item += para
            bullet_list += list_item

        self.node(bullet_list)

    def traceback(self, caption: str | None = None) -> None:
        # https://pygments.org/docs/lexers/#pygments.lexers.python.PythonTracebackLexer
        self.code(traceback.format_exc(), lang='pytb', caption=caption)

    def exception(
        self, e: Exception | BaseException, caption: str | None = None
    ) -> None:
        # A simplifed traceback.
        msg, cause, depth = str(e), e.__cause__, 1
        logger.warning('frist: %s', e.__cause__)
        while cause:
            msg += (
                '\n\n'
                + (depth - 1) * 2 * ' '
                + 'Caused by:\n'
                + depth * 2 * ' '
                + str(cause)
            )
            cause = cause.__cause__
            logger.warning('frist: %s', cause)
        # https://pygments.org/docs/lexers/#pygments.lexers.python.PythonTracebackLexer
        self.code(msg, lang='pytb', caption=caption)

    def current_exception(
        self, caption: str | None = None, traceback: bool = False
    ) -> None:
        if traceback:
            self.traceback(caption=caption)
        else:
            _, e, _ = sys.exc_info()
            if e is not None:
                self.exception(e, caption=caption)


    type Inliner = RstInliner | tuple[nodes.document, nodes.Element]

    def problematic(self, inliner: Inliner) -> nodes.problematic:
        """Create a cross-referenced inline problematic node."""

        if isinstance(inliner, RstInliner):
            prb = inliner.problematic('', '', self)
        else:
            # See also :meth:`docutils.parsers.rst.Inliner.problematic`.
            msgid = inliner[0].set_id(self, inliner[1])
            prb = nodes.problematic('', '', refid=msgid)
            prbid = inliner[0].set_id(prb)
            self.add_backref(prbid)

        prb += nodes.Text(' ')
        prb += nodes.superscript(self.title, self.title)

        return prb


@dataclass
class Reporter:
    """A helper class for storing :class:`Report` to nodes."""

    node: nodes.Element

    @property
    def reports(self) -> list[Report]:
        """Use ``node += Report('xxx')`` to append a report."""
        return [x for x in self.node if isinstance(x, Report)]

    def append(self, report: Report) -> None:
        self.node += report

    def clear(self, pred: Callable[[Report], bool] | None = None) -> list[Report]:
        """Clear report children from node if pred returns True."""
        msgs = []
        for report in self.reports:
            if not pred or pred(report):
                msgs.append(report)
                self.node.remove(report)
        return msgs

    def clear_empty(self) -> list[Report]:
        return self.clear(lambda x: x.empty())
