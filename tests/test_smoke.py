"""Smoke tests for sphinxnotes.render extension."""

import pytest


@pytest.mark.sphinx('html', testroot='ctxdir-usage')
def test_base_(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'My name is Shengyu Zhang' in html
