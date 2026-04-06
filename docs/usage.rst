=====
Usage
=====

This extension provides directives and roles for user to define, validate, and
render data.

.. highlight:: rst

.. _ext-usage-directives:

Directives
==========

.. rst:directive:: .. data.define:: name

   Define data and render it inplace.

   .. rst:directive:option:: *
      :type: depends on the schema

      This directive uses the "freestyle" option spec, if no any
      :rst:dir:`data.schema` applied, it allows arbitrary options to be specified.
      Otherwise, the option name and value is depends on the schema.

   The directive generates a dict-like data structure, we call it
   :ref:`context`, which looks like:

   .. example::
      :style: grid

      .. data.define:: mimi
         :color: black and brown

         I like fish!

   The fields of data context can be restricted and customized, see
   :rst:dir:`data.schema` for details.

   The data will be rendered by template defined by the previous
   :rst:dir:`data.template` directive.

.. rst:directive:: data.template

   Define a template for rendering data. The template will be applied to
   the subsequent :rst:dir:`data.define` directives.
   Refer to :doc:`tmpl` for guide of writing template.

   .. rst:directive:option:: on
      :type: choice

      Determinate :ref:`render-phases` of template. Defaults to ``parsing``.
      Available values: ``['parsing', 'parsed', 'resolving']``.

   .. rst:directive:option:: debug
      :type: flag

      Enable :ref:`debug report <debug>` for template rendering.

   .. rst:directive:option:: extra
      :type: space separted list

      List of :ref:`extra-context` to be used in the template.

   The content of the directive should be Jinja2 Template, please refer to
   ::doc:`tmpl`.

   Example:

   .. example::
      :style: grid

      .. data.template::

         Hi human! I am a cat named {{ name }}, I have {{ color }} fur.

         {{ content }}.

      .. data.define:: mimi
         :color: black and brown

         I like fish!


.. rst:directive:: .. data.schema:: <DSL>

   Define a schema for restricting data. The schema will be applied to the
   subsequent :rst:dir:`data.define` directives.
   We use a custom Domain Specified Language (DSL) to descript field's type,
   please refer to :doc:`dsl`.

   .. rst:directive:option:: *
      :type: <DSL>

      This directive uses the "freestyle" option spec, which allows arbitrary
      options to be specified. Each option corresponding to an option of
      :rst:dir:`data.define` directive.

      ``content: <DSL>``

   .. example::
      :style: grid

      .. data.schema:: int

      .. data.template::

         ``{{ name }} + 1 =  {{ name + 1 }}``

      .. data.define:: 1

.. rst:directive:: data.render

   Render a template immediately without defining data.
   This is useful when you want to render some fixed content or predefined data.

   .. rst:directive:option:: on
   .. rst:directive:option:: debug
   .. rst:directive:option:: extra

      The options of this directive are same to :rst:dir:`data.template`.

   .. example::
      :style: grid

      .. data.render::

         ``1 + 1 = {{ 1 + 1 }}``

.. _usage-custom-directive:

Defining Custom Directives
===========================

Instead of using :rst:dir:`data.define`, :rst:dir:`data.template`, and
:rst:dir:`data.schema` directives to define data in documents, you can define
custom directives in :file:`conf.py` using the :confval:`data_define_directives`
configuration option.

This is useful when you want to create a reusable directive with a fixed schema
and template across multiple documents.

First, add ``'sphinxnotes.render.ext'`` to your extension list like what we do in
:doc:`Getting Started <index>`.

Then add the following code to your :file:`conf.py`:

.. literalinclude:: conf.py
   :language: python
   :start-after: [example config start]
   :end-before: [example config end]

This creates a ``.. cat::`` directive that requires a name argument and accepts
a ``color`` options and a content. Use it in your document:

.. example::
   :style: grid

   .. cat:: mimi
      :color: black and brown

      I like fish!

For more details please refer to the :confval:`data_define_directives`
configuration value.
