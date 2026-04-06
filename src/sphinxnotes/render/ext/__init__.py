"""
sphinxnotes.render.ext
~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This is a POC (Proof of Concept) of the "sphinxnotes.render" extension.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .. import meta

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def setup(app: Sphinx):
    meta.pre_setup(app)

    app.setup_extension('sphinxnotes.render')

    from . import adhoc, derive, extractx, filters

    adhoc.setup(app)
    derive.setup(app)
    extractx.setup(app)
    filters.setup(app)

    return meta.post_setup(app)
