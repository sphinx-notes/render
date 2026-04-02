==========
Templating
==========

This page focuses on the context made available to templates, when that context
is available, and how extension authors can add more of it. You should already
be comfortable with basic Jinja2 syntax before reading this page.

.. _Jinja2: https://jinja.palletsprojects.com/en/stable/templates/

Jinja Environment
=================

Templates are rendered in a sandboxed Jinja2 environment.

- Undefined variables raise errors by default (``undefined=DebugUndefined``)
- Extension ``jinja2.ext.loopcontrols``, ``jinja2.ext.do`` are enabled by default.
- Output is plain markup text, so you can generate lists, directives, roles,
  and other reStructuredText constructs.

Built-in filters
----------------

``role``
   We provides a ``roles`` filter for producing role markup from a sequence of
   strings.

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

Extending filters
-----------------

To be done.

Context
=======

Directive and Role Context
--------------------------

When a directive or role provides data through
:py:class:`~sphinxnotes.render.BaseDataDefineDirective` or
:py:class:`~sphinxnotes.render.BaseDataDefineRole`, the template receives a
:py:class:`~sphinxnotes.render.ParsedData` object as its main context.

The following `template variables`_ are available in the main context:

.. _template variables: https://jinja.palletsprojects.com/en/stable/templates/#variables

.. note::

   We use the :rst:dir:`data.template` and :rst:dir:`data.define` directives from 
   :parsed_literal:`sphinxnotes.data__` for exampling.

   __ https://sphinx.silverrainz.me/data

.. glossary::

   ``{{ name }}``
      For directive, this refer to the directive argument.

      .. example::
         :style: grid

         .. data.template::

            {{ name }}

         .. data.define:: This is the argument

      For role, this is not available for now.

   ``{{ attrs.xxx }}``
      For directive, this refer to the directive options.
      It is a mapping of option's field to its value, so
      ``{{ attrs.label }}`` and ``{{ attrs['label'] }}`` are equivalent.

      .. example::
         :style: grid

         .. data.template::

            Label is {{ attrs.label }}.

         .. data.define::
            :label: Important

      For role, this is not available for now.

      .. note::

         Attribute values are also lifted to the top-level template context when
         there is no name conflict. For example, ``{{ label }}`` can be used
         instead of ``{{ attrs.label }}``, but ``{{ name }}`` still refers to
         the data object's own ``name`` field.

         .. example::
            :style: grid

            .. data.template::

               {{ label }} and {{ attrs.label }} are same.

            .. data.define::
               :label: Important

   ``{{ content }}``
      For directive, this refer to the directive body.

      .. example::
         :style: grid

         .. data.template::

            {{ content }}

         .. data.define::

            This is the body content.

      For role, this refer to the interpreted text.

      .. example::
         :style: grid

         .. data.template::

            {{ content }}

          :data:`This is the interpreted text`

The type of each variable depends on the corresponding :py:class:`~sphinxnote.render.Schema`.
For developers, the schema is provided by the
:py:meth:`sphinxnotes.render.BaseDataDefineDirective.current_schema` method.
For users, different extensions define the schema differently.
For example, for the `sphinxnotes.data` extension, the schema is defined through
the :rst:dir:`data.schema` directive.

Extra Context
-------------

Templates may also receive extra context entries in addition to the main data
context. These entries are stored under names prefixed with ``_``.

Built-in extra context
......................

.. list-table::
   :header-rows: 1

   * - Name
     - Available in
     - Description
   * - ``_sphinx``
     - all phases
     - A proxy to the Sphinx application object.
   * - ``_docutils``
     - all phases
     - A mapping that exposes registered docutils directives and roles.
   * - ``_markup``
     - parsing and later
     - Information about the current directive or role invocation, such as its
       type, name, source text, and line number.
   * - ``_section``
     - parsing and later
     - A proxy to the current section node, when one exists.
   * - ``_doc``
     - parsing and later
     - A proxy to the current document node.

These values are wrapped for safer template access. In practice this means
templates can read public, non-callable attributes, but should not rely on
arbitrary Python object behavior.

.. example::
   :style: grid

   .. data.render::

      Current document title is
      "{{ _doc.title }}".

Extending extra context
.......................

Extension authors can register more context generators through
:py:data:`sphinxnotes.render.REGISTRY`.

TODO.

Template
========

Render Phases
-------------

Each :py:class:`~sphinxnotes.render.Template` has a render phase controlled by
:py:class:`~sphinxnotes.render.Phase`.

``parsing`` (:py:data:`sphinxnotes.render.Phase.Parsing`)
   Render immediately while the directive or role is running.

   This is the default render phase.
   Choose this when the template only needs local information and does not rely
   on the final doctree or cross-document state.

   .. example::
      :style: grid

      .. data.render::
         :on: parsing

         - The current document has
           {{ _doc.sections | length }}
           section(s).
         - The current project has
           {{ _sphinx.env.all_docs | length }}
           document(s).

``parsed`` (:py:data:`sphinxnotes.render.Phase.Parsed`)
   Render after the current document has been parsed.

   Choose this when the template needs the complete doctree of the current
   document.

   .. example::
      :style: grid

      .. data.render::
         :on: parsed

         - The current document has
           {{ _doc.sections | length }}
           section(s).
         - The current project has
           {{ _sphinx.env.all_docs | length }}
           document(s).

``resolving`` (:py:data:`sphinxnotes.render.Phase.Resolving`)
   Render late in the build, after references and other transforms are being
   resolved.

   Choose this when the template depends on project-wide state or on document
   structure that is only stable near the end of the pipeline.

   .. example::
      :style: grid

      .. data.render::
         :on: resolving

         - The current document has
           {{ _doc.sections | length }}
           section(s).
         - The current project has
           {{ _sphinx.env.all_docs | length }}
           document(s).

Debugging
---------

Set :py:attr:`sphinxnotes.render.Template.debug` to ``True`` to append a debug
report to the rendered document. The report includes the resolved context,
available extra-context keys, the template source, the rendered markup text,
and the final nodes produced from that markup.

This is especially useful when a template fails because of an undefined
variable, unexpected data shape, or invalid generated markup.

End-to-End Example
==================

The following example shows a small custom directive that combines a schema and
template. The example is covered by a smoke test so the documentation stays in
sync with working code.

Extension code:

.. literalinclude:: ../tests/roots/test-strictdir-card/conf.py
   :language: python

Document source:

.. literalinclude:: ../tests/roots/test-strictdir-card/index.rst
   :language: rst
   :lines: 4-

Rendered result:

.. code-block:: rst

   .. rubric:: Template Guide

   .. important:: Featured entry

   :Tags: jinja, docs

   This page explains the template context.

This pattern is often the most convenient way to build small, declarative
directives. For more control, subclass
:py:class:`~sphinxnotes.render.BaseDataDefineDirective` directly and implement
``current_schema()`` and ``current_template()`` yourself.
