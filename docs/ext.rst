=========
Extending
=========

Extending the FDL
=================

You can extend the :doc:`dsl` by registering custom types, flags, and by-options
through the :py:attr:`~sphinxnotes.render.Registry.data` attribute of
:py:data:`sphinxnotes.render.REGISTRY`.

.. _add-custom-types:

Adding Custom Types
-------------------

Use :py:meth:`~sphinxnotes.render.data.REGISTRY.add_type` method of
:py:data:`sphinxnotes.render.REGISTRY` to add a new type:

>>> from sphinxnotes.render import REGISTRY, Field
>>> 
>>> def parse_color(v: str):
...     return tuple(int(x) for x in v.split(';'))
...
>>> def color_to_str(v):
...     return ';'.join(str(x) for x in v)
...
>>> REGISTRY.data.add_type('color', tuple, parse_color, color_to_str)
>>> Field.from_dsl('color').parse('255;0;0')
(255, 0, 0)

.. _add-custom-flags:

Adding Custom Flags
-------------------

Use :py:meth:`~sphinxnotes.render.data.Registry.add_flag` method of
:py:data:`sphinxnotes.render.REGISTRY` to add a new flag:

>>> from sphinxnotes.render import REGISTRY, Field
>>> REGISTRY.data.add_flag('unique', default=False)
>>> field = Field.from_dsl('int, unique')
>>> field.unique
True

.. _add-custom-by-options:

Adding Custom By-Options
------------------------

Use :py:meth:`~sphinxnotes.render.data.Registry.add_by_option` method of
:py:data:`sphinxnotes.render.REGISTRY` to add a new by-option:

>>> from sphinxnotes.render import REGISTRY, Field
>>> REGISTRY.data.add_by_option('group', str)
>>> field = Field.from_dsl('str, group by size')
>>> field.group
'size'
>>> REGISTRY.data.add_by_option('index', str, store='append')
>>> field = Field.from_dsl('str, index by month, index by year')
>>> field.index
['month', 'year']

.. _ext-extra-context:

Extending Extra Contexts
========================

Extra contexts are registered by a
:py:deco:`sphinxnotes.render.extra_context` class decorator.

The decorated class must be one of the following classes:
:py:class:`~sphinxnotes.render.ParsingPhaseExtraContext`,
:py:class:`~sphinxnotes.render.ParsedPhaseExtraContext`,
:py:class:`~sphinxnotes.render.ResolvingPhaseExtraContext`,
:py:class:`~sphinxnotes.render.GlobalExtraContext`.

.. literalinclude:: ../tests/roots/test-extra-context/conf.py
   :language: python
   :start-after: [literalinclude start]
   :end-before: [literalinclude end]

.. dropdown:: :file:`cat.json`

   .. literalinclude:: ../tests/roots/test-extra-context/cat.json

.. example::
   :style: grid

   .. data.render::
      :extra: cat

      {{ load_extra('cat').name }}

.. _ext-filters:

Extending ilters
=================

Template filters are registered by a
:py:deco:`sphinxnotes.render.filter` function decorator.

The decorated function takes a :py:class:`sphinx.environment.BuildEnvironment`
as argument and returns a filter function.

.. note::

   The decorator is used to **decorate the filter function factory, NOT
   the filter function itself**.

.. literalinclude:: ../tests/roots/test-filter-example/conf.py
   :language: python
   :start-after: [literalinclude start]
   :end-before: [literalinclude end]

.. example::
   :style: grid

   .. data.render::

      {{ "Hello world" | catify }}

.. _ext-directives:
.. _ext-roles:

Extending Directives/Roles
==========================

.. tip::

   Before reading this documentation, please refer to
   :external+sphinx:doc:`development/tutorials/extending_syntax`.
   See how to extend :py:class:`SphinxDirective` and :py:class:`SphinxRole`.

All of the classes listed in :ref:`api-directives` are subclassed from the
internal ``sphinxnotes.render.Pipeline`` class, which is responsible to generate
the dedicated :py:class:`node <sphinxnotes.render.pending_node>` that
carries a :ref:`context` and a :py:class:`~sphinxnotes.render.Template`.

At the appropriate :ref:`render-phases`, the node will be rendered into markup
text, usually reStructuredText. The rendered text is then parsed again by
Sphinx and inserted into the document.

.. seealso::

   - :doc:`tmpl` for template variables, phases, and extra context
   - :doc:`dsl` for the field description language used by
     :py:class:`~sphinxnotes.render.Field` and
     :py:class:`~sphinxnotes.render.Schema`
   - Implementations of :parsed_literal:`sphinxnotes-render.ext__`
     and :parsed_literal:`sphinxnotes-any__`.

   __ https://github.com/sphinx-notes/render/tree/master/src/sphinxnotes/render/ext
   __ https://github.com/sphinx-notes/any

Subclassing :py:class:`~sphinxnotes.render.BaseContextDirective`
----------------------------------------------------------------

Now we have a quick example to help you get Started.
:external+sphinx:doc:`Create a Sphinx documentation <tutorial/getting-started>`
with the following ``conf.py``:

.. literalinclude:: ../tests/roots/test-base-context-directive-example/conf.py

This is the smallest useful extension built on top of ``sphinxnotes.render``:

- it defines a mimi-dedicated directive by subclassing
  :py:class:`~sphinxnotes.render.BaseContextDirective`
- it returns a :py:class:`~sphinxnotes.render.ResolvedContext` object from
  ``current_context()``
- it returns a :py:class:`~sphinxnotes.render.Template` from
  ``current_template()``
- the template is rendered in the default
  :py:data:`~sphinxnotes.render.Phase.Parsing` phase

Now use the directive in your document:

.. example::
   :style: grid

   .. mimi::
 
Subclassing :py:class:`~sphinxnotes.render.BaseDataDefineDirective`
-------------------------------------------------------------------

``BaseDataDefineDirective`` is higher level of API than ``BaseContextDirective``.
You no longer need to implement the ``current_context`` methods; instead,
implement the :py:meth:`~sphinxnotes.render.BaseDataDefineDirective.current_schema`
method.

Here's an example:

.. literalinclude:: ../tests/roots/test-base-data-define-directive-example/conf.py

Key differences from ``BaseContextDirective``:

- The directive automatically generates :py:class:`~sphinxnotes.render.RawData`
  (from directive's arguments, options, and content, by method
  :py:meth:`~sphinxnotes.render.BaseDataDefineDirective.current_raw_data`).
- The generated RawData are parsed to :py:class:`~sphinxnotes.render.ParsedData`
  according to the :py:class:`~sphinxnotes.render.Schema` returned from
  :py:meth:`~sphinxnotes.render.BaseDataDefineDirective.current_schema` method.

  .. tip::

     Internally, the ``ParsedData`` is returned by ``current_context``, so
     we do not need to implement it.

- The the fields of schema are generated from :doc:`dsl` which restricted the
  ``color`` must be an space-separated list, and ``birth`` must be a integer.
- The ``current_template`` still returns a Jinja template, but it uses more fancy
  syntax.

Use the directive in your document:

.. example::
   :style: grid

   .. cat2:: mimi
      :color: black and brown
      :birth: 2025

      I like fish!

Subclassing :py:class:`~sphinxnotes.render.StrictDataDefineDirective`
----------------------------------------------------------------------

``StrictDataDefineDirective`` is an even higher-level API built on top of
``BaseDataDefineDirective``. It automatically handles ``SphinxDirective``'s members
from your :py:class:`~sphinxnotes.render.Schema`, so you don't need to manually
set:

- ``required_arguments`` / ``optional_arguments`` - derived from ``Schema.name``
- ``option_spec`` - derived from ``Schema.attrs`` 
- ``has_content`` - derived from ``Schema.content``

You no longer need to manually create subclasses, simply pass ``schema`` and
``template`` to :py:meth:`~sphinxnotes.render.StrictDataDefineDirective.derive`
method:

.. literalinclude:: ../tests/roots/test-strict-data-define-directive-example/conf.py

Use the directive in your document:

.. example::
   :style: grid

   .. cat3:: mimi
      :color: black and brown
      :birth: 2025

      I like fish!
