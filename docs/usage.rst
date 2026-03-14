=====
Usage
=====

.. seealso::

   Before reading this documentation, please refer to
   :external+sphinx:doc:`development/tutorials/extending_syntax`.
   see how to extends :py:class:`SphinxDirective` and :py:class:`SphinxRole`.

Create a Sphinx documentation with the following ``conf.py``:

.. literalinclude:: ../tests/roots/test-ctxdir-usage/conf.py

Now use the directive in your document:

.. code-block:: rst

   .. me::

This will render as: My name is Shengyu Zhang.

.. seealso:: See implementations of `sphinxnotes-any`__ and `sphinxnotes-data`__
   for more details

   __ https://github.com/sphinx-notes/any
   __ https://github.com/sphinx-notes/data
