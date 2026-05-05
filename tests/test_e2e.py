"""E2E tests for sphinxnotes.render extension."""

import pytest


@pytest.mark.sphinx('html', testroot='filter-example')
def test_custom_filter(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'I love you, meow~' in html


@pytest.mark.sphinx('html', testroot='strict-data-define-directive-example')
def test_strict_data_define_directive(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'Hi human! I am a cat named mimi, I have black and brown fur.' in html
    assert 'I like fish!' in html
    assert 'I am 1 years old.' in html
    assert 'Hi human! I am a cat named lucy, I have white fur.' in html
    assert 'I am 5 years old.' in html
    assert 'I like tuna!' in html


@pytest.mark.sphinx('html', testroot='base-data-define-directive-example')
def test_base_data_define_directive(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'Hi human! I am a cat named mimi, I have black and brown fur.' in html
    assert 'I like fish!' in html
    assert 'I am 1 years old.' in html
    assert 'Hi human! I am a cat named lucy, I have white fur.' in html
    assert 'I am 5 years old.' in html
    assert 'I like tuna!' in html


@pytest.mark.sphinx('html', testroot='base-context-directive-example')
def test_base_context_directive(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'Hi human! I am a cat named mimi, I have black and brown fur.' in html
    assert 'I like fish!' in html


@pytest.mark.sphinx('html', testroot='extra-context')
def test_extra_context_custom_loader(app, status, warning):
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'mimi' in html


@pytest.mark.sphinx('html', testroot='extra-context-rebuild')
def test_extra_context_rebuild(app, status, warning):
    app.build()
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'doc-sections=0' in html
    assert 'all-docs=1' in html


# ===========================
# Test sphinxnotes.render.ext
# ===========================

PHASES = ['parsing', 'parsed', 'resolving']


@pytest.mark.sphinx('html', testroot='data-define')
@pytest.mark.parametrize('phase', PHASES)
def test_render_ext_data_define_directives(app, status, warning, phase):
    """Test that data.template and data.define directives work correctly."""
    index_path = app.srcdir / 'index.rst'
    content = index_path.read_text(encoding='utf-8')
    modified_content = content.replace(':on: {phase}', f':on: {phase}', 1)
    index_path.write_text(modified_content, encoding='utf-8')

    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'RenderedName' in html
    assert 'RenderedAttr1' in html
    assert 'RenderedAttr2' in html
    assert 'RenderedValue1' in html
    assert 'RenderedValue2' in html
    assert 'RenderedContent' in html


@pytest.mark.sphinx('html', testroot='derive')
def test_derived_render_ext_data_define_directives(app, status, warning):
    """Test that render_ext_data_define_directives generates directives correctly."""
    app.build()

    html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert 'Custom: myname (type: mytype)' in html
    assert 'Error in “custom” directive: unknown option: “unkown”.'
