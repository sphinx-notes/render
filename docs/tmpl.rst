==========
Templating
==========

We use Jinja2_ to rendering templating to markup text (usually reStructuredText).
User should be familiar with Jinja2 before reading this document.

.. _Jinja2: https://jinja.palletsprojects.com/en/stable/templates/

.. _context:

Data Context
============

Context defined by directives and roles consist of following `template variables`_:

.. glossary::

   ``{{ name }}``
      For directive, it refer to the only argument, such as ``bar`` of
      ``.. foo:: bar``.

      For role, it refer to the name, such as ``foo`` of ``:foo:`bar```.

   ``{{ attrs.xxx }}``
      For directive, they refer to directive options 

      For role, it is usually empty.

      .. note::

         You can also refer them without the ``attr.`` prefix (just ``{{ xxx }}``)
         when there is no ambiguity.

   ``{{ content }}``
      For directive, it refers to the directive content.

      For role, it refer to the interpreted text, such as ``bar`` of ``:foo:`bar```.

The type of variables are depended on the corrsponding :doc:`dsl`.

.. hint:: For extension developers:

   Directive and roles refer to classes derived from
   :py:class:`~sphinxnotes.render.BaseDataDefineRole` and
   :py:class:`~sphinxnotes.render.BaseDataDefineDirective`.

   The aboved context is refer to :py:class:`~sphinxnotes.render.ParsedData`.

.. _template variables: https://jinja.palletsprojects.com/en/stable/templates/#variables

Extra Contexts
==============

Extra context can be extending by implmenting one of the following classs:

:py:class:`~sphinxnotes.render.GlobalExtraContxt`
:py:class:`~sphinxnotes.render.ParsePhaseExtraContext`
:py:class:`~sphinxnotes.render.TransformPhaseExtraContext`

Phases
======

:py:class:`sphinxnotes.render.Phase`.

.. example::
   :style: grid

   .. data:render::
      :on: parsing

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current proejct has
        {{ _sphinx.env.all_docs | length }} document(s).

.. example::
   :style: grid

   .. data:render::
      :on: parsed

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current proejct has
        {{ _sphinx.env.all_docs | length }} document(s).

.. example::
   :style: grid

   .. data:render::
      :on: resolving

      - The current document has
        {{ _doc.sections | length }} section(s).
      - The current proejct has
        {{ _sphinx.env.all_docs | length }} document(s).

TODO
====
