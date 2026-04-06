keep_warnings = True

extensions = ['sphinxnotes.render.ext']

render_ext_data_define_directives = {
    'custom': {
        'schema': {
            'name': 'str, required',
            'attrs': {'type': 'str'},
        },
        'template': {
            'on': 'parsing',
            'text': 'Custom: {{ name }} (type: {{ attrs.type }})',
        },
    },
}
