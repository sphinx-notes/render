==========
Templating
==========

This guide explains how to write Jinja2_ templates for the
``sphinxnotes.render``-based extension (``sphinxnotes.render.ext``,
``sphinxnotes.any`` and etc.). You should already be comfortable with basic
Jinja2 syntax before reading this page.

.. _Jinja2: https://jinja.palletsprojects.com/en/stable/templates/

What is a Template
==================

A template is a Jinja2 text that defines how structured data is converted into
reStructuredText or Markdown markup. The rendered text is then parsed by Sphinx
and inserted into the document.

The way of defining template will vary depending on the extension you use.
For ``sphinxnotes.render.ext``, you can use :rst:dir:`data.template` or
:confval:`render_ext_data_define_directives`.

.. tip::

   Internally, template is a :py:class:`~sphinxnotes.render.Template` object.
   It is provide by method
   :py:meth:`BaseDataDefineDirective.current_template() <sphinxnotes.render.BaseDataDefineDirective.current_template>` 
   or
   :py:meth:`BaseDataDefineRole.current_template() <sphinxnotes.render.BaseDataDefineRole.current_template>` 


What Data is Available
======================

Your template receives data from two sources: **main context** and **extra
context**.

.. _context:

Main Context
------------

When you define data through a directive (such as :rst:dir:`data.define`) or
role in your document, the template receives that data as its main context.
This is the data explicitly provided by the markup itself.

For example, when you use the ``data.define`` directive, the generated main
context looks like the Python dict on the right:

.. example::
   :style: grid

   .. data.define:: mimi
      :color: black and brown

      I like fish!

The template receives the argument (``mimi``), options (``:color: black ...``),
and body content (``I like fish!``) as the main context.

The following `template variables`_ are available:

.. _template variables: https://jinja.palletsprojects.com/en/stable/templates/#variables

.. glossary::

   ``{{ name }}``
      For directives, this refers to the directive argument.

      .. example::
         :style: grid

         .. data.template::

            {{ name }}

         .. data.define:: This is the argument

      For roles, this is not available.

   ``{{ attrs }}``
      For directives, this refers to directive options. It is a mapping of
      option field to value, so ``{{ attrs.label }}`` and
      ``{{ attrs['label'] }}`` are equivalent.

      .. example::
         :style: grid

         .. data.template::

            Label is {{ attrs.label }}.

         .. data.define::
            :label: Important

      For roles, this is not available.

      Attribute values are lifted to the top-level template context when there
      is no name conflict. For example, ``{{ label }}`` can be used instead of
      ``{{ attrs.label }}``:

      .. example::
         :style: grid

         .. data.template::

            Label is {{ label }}.

         .. data.define::
            :label: Important

   ``{{ content }}``
      For directives, this refers to the directive body.

      .. example::
         :style: grid

         .. data.template::

            {{ content }}

         .. data.define::

            This is the body content.

      For roles, this refers to the interpreted text.

      .. example::
         :style: grid

         .. data.template::

            {{ content }}

          :data:`This is the interpreted text`

The type of each variable depends on the corresponding schema. Different
extensions define schemas differently. For example, the ``sphinxnotes.render.ext``
extension defines the schema through the :rst:dir:`data.schema` directive or
``schema`` field of :confval:`render_ext_data_define_directives`.

.. tip::

   Internally, Main context is a :py:class:`~sphinxnotes.render.ParsedData`
   object.

   Directive or role subclassed from
   :py:class:`~sphinxnotes.render.BaseDataDefineDirective` or
   :py:class:`~sphinxnotes.render.BaseDataDefineRole` can generate main context.

.. _extra-context:

Extra Context
-------------

Extra context provides access to pre-prepared structured data from external
sources (such as Sphinx application, JSON file, and etc.). Unlike main context
which comes from the directive/role itself, extra context lets you fetch data
that was prepared beforehand.

Extra contexts are typically generated on demand at different construction stages,
so you need to declare them in advance, and load it in the template using the
``load_extra()`` function:

The way of declaring extra context is vary depending on the extension you use.
For ``sphinxnotes.render.ext`` extension, :rst:dir:`data.template:extra`,
:rst:dir:`data.render:extra` and the ``templat.extra`` field of
:confval:`render_ext_data_define_directives` are for this.

.. example::
   :style: grid

   .. data.render::
      :extra: doc

      {% set doc = load_extra('doc') %}

      Document Title: "{{ doc.title }}"

Built-in Extra Contexts
~~~~~~~~~~~~~~~~~~~~~~~

The following extra contexts are available:

``sphinx``
   :Phase: all

   A proxy to the :py:class:`sphinx.application.Sphinx` object.

   .. example::
      :style: grid

      .. data.render::
         :extra: sphinx

         {% set app = load_extra('sphinx') %}

         **{{ app.extensions | length }}**
         extensions are loaded.

``env``
   :Phase: all

   A proxy to the :py:class:`sphinx.environment.BuildEnvironment` object.

   .. example::
      :style: grid

      .. data.render::
         :extra: env

         {% set env = load_extra('env') %}

         **{{ env.all_docs | length }}**
         documents found.

``markup``
   :Phase: parsing and later

   Information about the current directive or role invocation, such as its
   type, name, source text, and line number.

   .. example::
      :style: grid

      .. data.render::
         :extra: markup

         {%
         set m = load_extra('markup')
                 | jsonify
         %}

         .. code::

            {% for line in m.split('\n') -%}
            {{ line }}
            {% endfor %}
 
``section``
   :Phase: parsing and later

   A proxy to the current :py:class:`docutils.nodes.section` node, when one
   exists.

   .. example::
      :style: grid

      .. data.render::
         :extra: section

          Section Title:
         "{{ load_extra('section').title }}"

``doc``
   :Phase: parsing and later

   A proxy to the current :py:class:`docutils.notes.document` node.

   .. example::
      :style: grid

      .. data.render::
         :extra: doc

         Document title:
         "{{ load_extra('doc').title }}".

.. seealso:: :ref:`ext-extra-context`

TODO: the proxy object.

Built-in Filters
================

In addition to the `Builtin Jinia Filters`__, this extension also provides the
following filters:

__ https://jinja.palletsprojects.com/en/stable/templates/#builtin-filters

``roles``
   Produces role markup from a sequence of strings.

   .. example::
      :style: grid

      .. data.render::

         {%
         set text = ['index', 'usage']
                    | roles('doc')
                    | join(', ')
         %}

         :Text: ``{{ text }}``
         :Rendered: {{ text }}

``jsonify``
   Convert value to JSON.

   .. example::
      :style: grid

      .. data.render::

         {% set text = {'name': 'mimi'} %}

         :Strify: ``{{ text }}``
         :JSONify: ``{{ text | jsonify }}``

.. seealso:: :ref:`ext-filters`

.. _render-phases:

Render Phases
=============

Each template has a render phase that determines when it is processed:

.. glossary::

   ``parsing``
      Render immediately while the directive or role is running. This is the
      default.

      Choose this when the template only needs local information and does not
      rely on the final doctree or cross-document state.

      .. example::
         :style: grid

         .. data.render::
            :on: parsing
            :extra: doc env

            {% set doc = load_extra('doc') %}
            {% set env = load_extra('env') %}

            - The current document has
              {{ doc.sections | length }}
              section(s).
            - The current project has
              {{ env.all_docs | length }}
              document(s).

   ``parsed``
      Render after the current document has been parsed.

      Choose this when the template needs the complete doctree of the current
      document.

      .. example::
         :style: grid

         .. data.render::
            :on: parsed
            :extra: doc env

            {% set doc = load_extra('doc') %}
            {% set env = load_extra('env') %}

            - The current document has
              {{ doc.sections | length }}
              section(s).
            - The current project has
              {{ env.all_docs | length }}
              document(s).

   ``resolving``
      Render late in the build, after references and other transforms are being
      resolved.

      Choose this when the template depends on the document structure that is
      only stable near the end of the pipeline.

      .. example::
         :style: grid

         .. data.render::
            :on: resolving
            :extra: doc env

            {% set doc = load_extra('doc') %}
            {% set env = load_extra('env') %}

            - The current document has
              {{ doc.sections | length }}
              section(s).
            - The current project has
              {{ env.all_docs | length }}
              document(s).

.. tip::

   Internally, each phase corresponds to a :py:class:`~sphinxnotes.render.Phase`
   enum value. The ``on`` option maps to :py:attr:`~sphinxnotes.render.Template.phase`.

.. _debug:

Debugging
=========

Enable the debug option to see a detailed report when troubleshooting templates:

.. example::
   :style: grid

   .. data.render::
      :debug:

      {{ 1 + 1 }}

This is especially useful when a template fails due to an undefined variable,
unexpected data shape, or invalid generated markup.

Some Technical Details
======================

Jinja Template 
--------------

Templates are rendered in a sandboxed Jinja2 environment.

- Undefined variables raise errors by default (``undefined=DebugUndefined``)
- Extension ``jinja2.ext.loopcontrols``, ``jinja2.ext.do`` are enabled by default.
