from sphinxnotes.render.jinja import TemplateRenderer


def test_template_renderer_injects_template_globals():
    text = "{{ load_extra('cat') }}"

    rendered = TemplateRenderer(text).render(
        {},
        globals={'load_extra': lambda name: f'loaded:{name}'},
    )

    assert rendered == 'loaded:cat'
