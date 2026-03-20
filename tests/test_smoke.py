"""Smoke tests for sphinxnotes.render extension."""

import pytest


@pytest.mark.sphinx('html', testroot='ctxdir-usage')
def test_base_(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'My name is Shengyu Zhang' in html


# -- literalinclude:start:end-to-end-card --
@pytest.mark.sphinx('html', testroot='strictdir-card')
def test_strict_data_define_directive_card(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'Template Guide' in html
    assert 'Featured entry' in html
    assert 'jinja, docs' in html
    assert 'This page explains the template context.' in html


# -- literalinclude:end:end-to-end-card --
