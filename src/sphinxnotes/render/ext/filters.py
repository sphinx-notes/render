"""
sphinxnotes.render.ext.filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

Provides useful Jinja2 template filter.

"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterable
import json

from .. import meta, filter

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment


@filter('roles')
def roles(_: BuildEnvironment):
    """
    Converting list of string to list of reStructuredText role.

    For example::

        {{ ["foo", "bar"] | roles("doc") }}

    Produces ``[":doc:`foo`", ":doc:`bar`"]``.
    """

    def _filter(value: Iterable[str], role: str) -> Iterable[str]:
        return map(lambda x: ':%s:`%s`' % (role, x), value)

    return _filter


@filter('jsonify')
def jsonify(_: BuildEnvironment):
    """Converting value to JSON."""

    def _filter(value: Any) -> Any:
        return json.dumps(value, indent='  ')

    return _filter


def setup(app: Sphinx):
    meta.pre_setup(app)
    return meta.post_setup(app)
