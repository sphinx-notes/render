==============
API References
==============

Value, Data, Field and Schema
=============================

.. autoclass:: sphinxnotes.render.PlainValue
.. autoclass:: sphinxnotes.render.Value

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

The Render Pipeline
===================

Context
-------

.. autoclass:: sphinxnotes.render.PendingContext
.. autotype:: sphinxnotes.render.ResolvedContext
.. autoclass:: sphinxnotes.render.UnparsedData

.. autoclass:: sphinxnotes.render.pending_node

Extra Context
-------------

.. autoclass:: sphinxnotes.render.ExtraContextGenerator
.. autoclass:: sphinxnotes.render.ExtraContextRegistry

Template
--------

.. autoclass:: sphinxnotes.render.Template
.. autoclass:: sphinxnotes.render.Phase

Pipeline
--------

.. autoclass:: sphinxnotes.render.BaseContextRole
.. autoclass:: sphinxnotes.render.BaseContextDirective
.. autoclass:: sphinxnotes.render.BaseDataDefineRole
.. autoclass:: sphinxnotes.render.BaseDataDefineDirective
.. autoclass:: sphinxnotes.render.StrictDataDefineDirective

Registry
========

.. autodata:: sphinxnotes.render.REGISTRY

.. autoclass:: sphinxnotes.render.Registry

   .. autoproperty:: data
   .. autoproperty:: extra_context
