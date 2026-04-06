==============
API References
==============

.. _api-directives:
.. _api-roles:

Roles and Directives
====================

.. seealso::

   For a minimal end-to-end example of creating your own directive, start with
   :ref:`ext-directives`.

Base Role Classes
-----------------

.. autoclass:: sphinxnotes.render.BaseContextRole
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_context, current_template

.. autoclass:: sphinxnotes.render.BaseDataDefineRole
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_schema, current_template

Base Directive Classes
----------------------

.. autoclass:: sphinxnotes.render.BaseContextDirective
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_raw_data, current_context, current_template

.. autoclass:: sphinxnotes.render.BaseDataDefineDirective
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_raw_data, current_schema, current_template

.. autoclass:: sphinxnotes.render.StrictDataDefineDirective
   :show-inheritance:
   :members: derive

Node
=====

.. autoclass:: sphinxnotes.render.pending_node

.. _api-context:

Context
=======

Context refers to the dynamic content of a Jinja template. It can be:

:py:class:`~sphinxnotes.render.ResolvedContext`:
  Our dedicated data type (:py:class:`sphinxnotes.render.ParsedData`), or any
  Python ``dict``.

:py:class:`~sphinxnotes.render.PendingContext`:
   Context that is not yet available. For example, it may contain
   :py:class:`unparsed data <sphinxnotes.render.RawData>`,
   remote data, and more.

   :py:class:`PendingContext` can be resolved to
   :py:class:`~sphinxnotes.render.ResolvedContext` by calling
   :py:meth:`~sphinxnotes.render.PendingContext.resolve`.

.. autotype:: sphinxnotes.render.ResolvedContext

.. autoclass:: sphinxnotes.render.PendingContext
   :members: resolve

``PendingContext`` Implementations
----------------------------------

.. autoclass:: sphinxnotes.render.UnparsedData
   :show-inheritance:

.. _extractx:

Template
========

See :doc:`tmpl` for the higher-level guide.

.. autoclass:: sphinxnotes.render.Template
   :members:

.. autoclass:: sphinxnotes.render.Phase
   :members:

Extra Context
=============

See :doc:`tmpl` for built-in extra-context names such as ``doc`` and
``sphinx``, plus usage examples.

.. autodecorator:: sphinxnotes.render.extra_context

.. autoclass:: sphinxnotes.render.ParsingPhaseExtraContext
   :members: phase, generate
   :undoc-members:

.. autoclass:: sphinxnotes.render.ParsedPhaseExtraContext
   :members: phase, generate
   :undoc-members:

.. autoclass:: sphinxnotes.render.ResolvingPhaseExtraContext
   :members: phase, generate
   :undoc-members:

.. autoclass:: sphinxnotes.render.GlobalExtraContext
   :members: phase, generate
   :undoc-members:

Filters
=======

.. autodecorator:: sphinxnotes.render.filter

Data, Field and Schema
======================

.. autotype:: sphinxnotes.render.PlainValue

.. autotype:: sphinxnotes.render.Value

.. autoclass:: sphinxnotes.render.RawData
   :members: name, attrs, content
   :undoc-members:

.. autoclass:: sphinxnotes.render.ParsedData
   :members: name, attrs, content
   :undoc-members:

.. autoclass:: sphinxnotes.render.Field
   :members: parse

.. autoclass:: sphinxnotes.render.Schema
   :members: name, attrs, content
   :undoc-members:

.. autoclass:: sphinxnotes.render.data.Registry
   :members:

   .. autotype:: sphinxnotes.render.data.ByOptionStore

Registry
========

Developers can extend this extension (for example, to support more data types
or add new extra context) by adding new items to
:py:class:`sphinxnotes.render.REGISTRY`.

.. autodata:: sphinxnotes.render.REGISTRY

.. autoclass:: sphinxnotes.render.Registry

   .. autoproperty:: data
