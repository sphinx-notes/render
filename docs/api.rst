==============
API References
==============

The Render Pipeline
===================

The pipeline defines how nodes carrying data are generated and when they are
rendered as part of the document.

1. Generation: :py:class:`~sphinxnotes.render.BaseContextRole`,
   :py:class:`~sphinxnotes.render.BaseContextDirective` and their subclasses
   create :py:class:`~sphinxnotes.render.pending_node` on document parsing,
   and the node will be inserted to the document tree. The node contains:

   - :ref:`context`, the dynamic content of a Jinja template

   - :py:class:`~sphinxnotes.render.Template`,
     the Jinja template for rendering context to markup text
     (reStructuredText or Markdown)

2. Render: the ``pending_node`` node will be rendered at the appropriate
   :py:class:`~sphinxnotes.render.Phase`, depending on
   :py:attr:`~sphinxnotes.render.pending_node.template.phase`.

Node
-----

.. autoclass:: sphinxnotes.render.pending_node

.. _context:

Context
-------

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: sphinxnotes.render.UnparsedData
   :show-inheritance:

.. _extractx:

Template
--------

.. autoclass:: sphinxnotes.render.Template
   :members:

.. autoclass:: sphinxnotes.render.Phase
   :members:

Extra Context
-------------

.. autoclass:: sphinxnotes.render.GlobalExtraContxt

.. autoclass:: sphinxnotes.render.ParsePhaseExtraContext

.. autoclass:: sphinxnotes.render.ResolvePhaseExtraContext

.. autoclass:: sphinxnotes.render.ExtraContextRegistry
   :members:


Base Roles and Directives
-------------------------

Base Role Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: sphinxnotes.render.BaseContextRole
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_context, current_template

.. autoclass:: sphinxnotes.render.BaseDataDefineRole
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_schema, current_template

Base Directive Classes
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: sphinxnotes.render.BaseContextDirective
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_context, current_template

.. autoclass:: sphinxnotes.render.BaseDataDefineDirective
   :show-inheritance:
   :members: process_pending_node, queue_pending_node, queue_context, current_schema, current_template

.. autoclass:: sphinxnotes.render.StrictDataDefineDirective
   :show-inheritance:
   :members: derive

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
   .. autoproperty:: extra_context
