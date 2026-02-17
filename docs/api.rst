=============
API Reference
=============

Data Types
==========

.. autotype:: sphinxnotes.render.PlainValue
.. autotype:: sphinxnotes.render.Value

.. autoclass:: sphinxnotes.render.RawData
.. autoclass:: sphinxnotes.render.ParsedData

.. autoclass:: sphinxnotes.render.Field
.. autoclass:: sphinxnotes.render.Schema

.. autoclass:: sphinxnotes.render.data.Registry

   .. automethod:: add_type
   .. automethod:: add_form
   .. automethod:: add_flag
   .. automethod:: add_by_option

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
