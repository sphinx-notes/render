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


@filter('roles')
def roles(value: Iterable[str], role: str) -> Iterable[str]:
    """Converting list of string to list of reStructuredText role.

    For example::

        {{ ["foo", "bar"] | roles("doc") }}

    Produces ``[":doc:`foo`", ":doc:`bar`"]``.
    """
    return map(lambda x, role=role: ':%s:`%s`' % (role, x), value)


@filter('jsonify')
def jsonify(value: Any, indent: str | None = None) -> Any:
    """Converting value to JSON."""
    return json.dumps(value, indent=indent)


def setup(app: Sphinx):
    meta.pre_setup(app)
    return meta.post_setup(app)
