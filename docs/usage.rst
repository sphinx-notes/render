=====
Usage
=====

.. seealso::

   Before reading this documentation, please refer to
   :external+sphinx:doc:`development/tutorials/extending_syntax`.
   See how to extend :py:class:`SphinxDirective` and :py:class:`SphinxRole`.

``sphinxnotes.render`` uses Jinja2_ to turn structured data into markup
text, usually reStructuredText. The rendered text is then parsed again by
Sphinx and inserted into the document.

.. _Jinja2: https://jinja.palletsprojects.com/en/stable/templates/

Now we have a quick example to help you get Started.
Create a Sphinx documentation with the following ``conf.py``:

.. literalinclude:: ../tests/roots/test-ctxdir-usage/conf.py

This is the smallest useful extension built on top of ``sphinxnotes.render``:

- it defines a custom directive by subclassing
  :py:class:`~sphinxnotes.render.BaseContextDirective`
- it returns a context object from ``current_context()``
- it returns a :py:class:`~sphinxnotes.render.Template` from
  ``current_template()``
- the template is rendered in the default
  :py:data:`~sphinxnotes.render.Phase.Parsing` phase

Now use the directive in your document:

.. example::
   :style: grid

   .. me::
 
Next steps
==========

Once you understand this minimal example, the rest of the workflow is usually:

1. define a :py:class:`~sphinxnotes.render.Schema` so your directive input is
   parsed into structured values
2. write a Jinja template that consumes that structured context
3. choose an appropriate :py:class:`~sphinxnotes.render.Phase` when the
   template needs document-level or project-level information
4. add custom extra context if built-in variables are not enough

See also:

- :doc:`tmpl` for template variables, phases, and extra context
- :doc:`dsl` for the field description language used by
  :py:class:`~sphinxnotes.render.Field` and
  :py:class:`~sphinxnotes.render.Schema`
- :doc:`api` for the full Python API

.. seealso:: See implementations of `sphinxnotes-any`__ and `sphinxnotes-data`__
   for more details

   __ https://github.com/sphinx-notes/any
   __ https://github.com/sphinx-notes/data
