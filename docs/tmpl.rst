==========
Templating
==========

``sphinxnotes.render`` uses Jinja2_ to turn structured context data into markup
text, usually reStructuredText. The rendered text is then parsed again by
Sphinx/docutils and inserted into the document.

This page focuses on the context made available to templates, when that context
is available, and how extension authors can add more of it. You should already
be comfortable with basic Jinja2 syntax before reading this page.

.. _Jinja2: https://jinja.palletsprojects.com/en/stable/templates/

Jinja Environment
=================

Templates are rendered in a sandboxed Jinja2 environment.

- Undefined variables raise errors by default, which helps catch template
  mistakes early.
- Jinja loop control statements (``break`` and ``continue``) are enabled.
- The ``do`` extension is enabled.
- Output is plain markup text, so you can generate lists, directives, roles,
  and other reStructuredText constructs.

Built-in filters
----------------

``sphinxnotes.render`` provides a ``roles`` filter for producing role markup
from a sequence of strings.

.. code-block:: jinja

   {{ ['intro', 'usage'] | roles('doc') | join(', ') }}

This renders to text similar to:

.. code-block:: rst

   :doc:`intro`, :doc:`usage`

Data Context
============

When a directive or role provides data through
:py:class:`~sphinxnotes.render.BaseDataDefineDirective` or
:py:class:`~sphinxnotes.render.BaseDataDefineRole`, the template receives a
:py:class:`~sphinxnotes.render.ParsedData` object as its main context.

The following template variables are available:

.. glossary::

   ``{{ name }}``
      The parsed ``name`` field of the current data object.

      For directives, this usually comes from the directive argument. For roles,
      it usually comes from the role name or role input, depending on how the
      context source is implemented.

   ``{{ attrs.xxx }}``
      A parsed attribute value from the current data object.

      ``attrs`` is a mapping of attribute names to parsed values, so
      ``{{ attrs.color }}`` and ``{{ attrs['color'] }}`` are equivalent.

      .. note::

         Attribute values are also lifted to the top-level template context when
         there is no name conflict. For example, ``{{ color }}`` can be used
         instead of ``{{ attrs.color }}``, but ``{{ name }}`` still refers to
         the data object's own ``name`` field.

   ``{{ content }}``
      The parsed body content of the current data object.

      For directives, this is usually the directive body. For roles, this is
      usually the role text. If the schema does not define content, the value is
      ``None``.

The type of each variable depends on the corresponding :doc:`dsl` declaration.
For example, ``list of int`` becomes a Python list of integers, and ``bool``
becomes a Python boolean.

Example
-------

Given a schema like this:

.. code-block:: python

   Schema(
       name='str, required',
       attrs={
           'tags': 'list of str',
           'draft': 'bool',
       },
       content='str',
   )

the template can use:

.. code-block:: jinja

   {{ name }}
   {{ attrs.tags | join(', ') }}
   {{ draft }}
   {{ content }}

.. hint:: For extension developers:

   Derive from :py:class:`~sphinxnotes.render.BaseDataDefineDirective` or
   :py:class:`~sphinxnotes.render.BaseDataDefineRole` to create your own data
   source.

   The context described in this section corresponds to
   :py:class:`~sphinxnotes.render.ParsedData`.

.. _template variables: https://jinja.palletsprojects.com/en/stable/templates/#variables

Extra Context
=============

Templates may also receive extra context entries in addition to the main data
context. These entries are stored under names prefixed with ``_``.

Built-in extra context
----------------------

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

Example
-------

.. code-block:: jinja

   Current markup: {{ _markup.type }} {{ _markup.name }}
   Current document sections: {{ _doc.sections | length }}

Extending extra context
-----------------------

Extension authors can register more context generators through
:py:data:`sphinxnotes.render.REGISTRY`.

.. code-block:: python

   from sphinxnotes.render import REGISTRY, ParsePhaseExtraContext


   class ProjectContext(ParsePhaseExtraContext):
       def generate(self, host):
           return {'lineno': host.lineno}


   REGISTRY.extra_context.add_parsing_phase_context('project', ProjectContext())

The registered context becomes available in templates as ``_project``.

Depending on when the value can be computed, implement one of these base
classes:

- :py:class:`~sphinxnotes.render.GlobalExtraContxt` for context available in
  every phase.
- :py:class:`~sphinxnotes.render.ParsePhaseExtraContext` for context generated
  during :py:data:`~sphinxnotes.render.Phase.Parsing`.
- :py:class:`~sphinxnotes.render.ResolvePhaseExtraContext` for context generated
  during :py:data:`~sphinxnotes.render.Phase.Parsed` or
  :py:data:`~sphinxnotes.render.Phase.Resolving`.

Phases
======

Each :py:class:`~sphinxnotes.render.Template` has a render phase controlled by
:py:class:`~sphinxnotes.render.Phase`.

``parsing``
   Render immediately while the directive or role is running.

   Choose this when the template only needs local information and does not rely
   on the final doctree or cross-document state.

``parsed``
   Render after the current document has been parsed.

   Choose this when the template needs the complete doctree of the current
   document.

``resolving``
   Render late in the build, after references and other transforms are being
   resolved.

   Choose this when the template depends on project-wide state or on document
   structure that is only stable near the end of the pipeline.

Examples
--------

The following examples all use the same template text, but render it at
different phases:

.. example::
   :style: grid

   .. data.render::
      :on: parsing

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current project has
        {{ _sphinx.env.all_docs | length }} document(s).

.. example::
   :style: grid

   .. data.render::
      :on: parsed

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current project has
        {{ _sphinx.env.all_docs | length }} document(s).

.. example::
   :style: grid

   .. data.render::
      :on: resolving

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current project has
        {{ _sphinx.env.all_docs | length }} document(s).

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

Debugging Templates
===================

Set :py:attr:`sphinxnotes.render.Template.debug` to ``True`` to append a debug
report to the rendered document. The report includes the resolved context,
available extra-context keys, the template source, the rendered markup text,
and the final nodes produced from that markup.

This is especially useful when a template fails because of an undefined
variable, unexpected data shape, or invalid generated markup.
