==========================
Field Description Language
==========================

.. default-domain:: py
.. highlight:: python
.. role:: py(code)
   :language: Python


The Field Description Language is a Domain Specific Language (DSL) that is used to
define the type and structure of field values. An FDL declaration consists of
one or more :term:`modifier` entries separated by commas (``,``).

Syntax
======

.. productionlist::
   dsl          : modifier ("," modifier)*
   modifier     : type_modifier | form_modifier | flag | by_option

.. glossary::

   Modifier
      There are four categories of modifiers:

   Type modifier
      Specifies the element type (scalar value)

   Form modifier
      Specifies a container type with element type

   Flag
      A boolean flag (either on or off)

   By-Option
      A key-value option

Python API
==========

Users can create a :class:`sphinxnotes.render.Field` from FDL and use it to parse
strings into :type:`sphinxnotes.render.Value`:

>>> from sphinxnotes.render import Field
>>> Field.from_dsl('list of int').parse('1,2,3')
[1, 2, 3]


Type
====

A type modifier specifies the data type of a single (scalar) value.

.. list-table::
   :header-rows: 1

   * - Modifier
     - Type
     - Aliases
     - Description
   * - ``bool``
     - :py:class:`bool`
     - ``flag``
     - Boolean: ``true``/``yes``/``1``/``on``/``y`` → True, ``false``/``no``/``0``/``off``/``n`` → False
   * - ``int``
     - :py:class:`int`
     - ``integer``
     - Integer
   * - ``float``
     - :py:class:`float`
     - ``number``, ``num``
     - Floating-point number
   * - ``str``
     - :py:class:`str`
     - ``string``
     - String. If it looks like a Python literal (e.g., ``"hello"``), it is parsed accordingly.

Examples:

======= ========= =============
DSL     Input     Result
------- --------- -------------
``int`` ``42``    :py:`42`
``str`` ``hello`` :py:`"hello"`
======= ========= =============

Form
====

A form modifier specifies a container type with its element type, using
``<form> of <type>`` syntax.

.. list-table::
   :header-rows: 1

   * - Modifier
     - Container
     - Separator
     - Description
   * - ``list of <type>``
     - :py:class:`list`
     - ``,``
     - Comma-separated list
   * - ``lines of <type>``
     - :py:class:`list`
     - ``\n``
     - Newline-separated list
   * - ``words of <type>``
     - :py:class:`list`
     - whitespace
     - Whitespace-separated list
   * - ``set of <type>``
     - :py:class:`set`
     - whitespace
     - Whitespace-separated set (unique values)

Examples:

================ =========== =====================
DSL              Input       Result
---------------- ----------- ---------------------
``list of int``  ``1, 2, 3`` :py:`[1, 2, 3]`
``lines of str`` ``a\nb``    :py:`['a', 'b']`
``words of str`` ``a b c``   :py:`['a', 'b', 'c']`
================ =========== =====================

Flag
====

A flag is a boolean modifier that can be either on or off.

Every flag is available as an attribute of the :class:`Field`.
For example, we have a "required" flag registered, and we can access ``Field.required``
attribute.

.. list-table::
   :header-rows: 1

   * - Modifier
     - Aliases
     - Default
     - Description
   * - ``required``
     - ``require``, ``req``
     - ``False``
     - Field must have a value

Examples::

    int, required

By-Option
=========

A by-option is a key-value modifier with the syntax ``<name> by <value>``.

Every by-option is available as an attribute of the :class:`Field`.
For example, we have a "sep" by-option registered, and we can get the separator
from ``Field.sep`` attribute.

Built-in by-options:

.. list-table::
   :header-rows: 1

   * - Modifier
     - Type
     - Description
   * - ``sep by '<sep>'``
     - :py:class:`str`
     - Custom separator for value form. Implies ``list`` if no form specified.

Examples:

=================== ========= ================
DSL                 Input     Result
------------------- --------- ----------------
``str, sep by '|'`` ``a|b``   :py:`['a', 'b']`
``int, sep by ':'`` ``1:2:3`` :py:`[1, 2, 3]`
=================== ========= ================

