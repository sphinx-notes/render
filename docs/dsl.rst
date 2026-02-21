=====================
Field Declaration DSL
=====================

.. default-domain:: py
.. highlight:: python
.. role:: py(code)
   :language: Python


The Field Declaration DSL is a Domain Specific Language (DSL) that used to
define the type and structure of field values. A DSL declaration consists of
one or more :term:`modifier`\ s separated by commas (``,``).

Python API
==========

User can create a :class:`sphinxnotes.render.Field` from DSL and use it to parse
string to :type:`sphinxnotes.render.Value`:

>>> from sphinxnotes.render import Field
>>> Field.from_dsl('list of int').parse('1,2,3')
[1, 2, 3]

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
     - String. If looks like a Python literal (e.g., ``"hello"``), it's parsed accordingly.

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

Every flag is available as a attribute of the :class:`Field`.
For example, we have a "required" flag registed, we can access ``Field.required``
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

Every by-option is available as a attribute of the :class:`Field`.
For example, we have a "sep" flag registed, we can get the value of separator
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

Extending the DSL
=================

You can extend the DSL by registering custom types, flags, and by-options
through the :attr:`~sphinxnotes.render.Registry.data` attribute of
:data:`sphinxnotes.render.REGISTRY`.

.. _add-custom-types:

Adding Custom Types
-------------------

Use :meth:`~sphinxnotes.render.data.REGISTRY.add_type` method of
:data:`sphinxnotes.render.REGISTRY` to add a new type:

>>> from sphinxnotes.render import REGISTRY
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

Use :meth:`~sphinxnotes.render.data.Registry.add_flag` method of
:data:`sphinxnotes.render.REGISTRY` to add a new type:

>>> from sphinxnotes.render import REGISTRY
>>> REGISTRY.data.add_flag('unique', default=False)
>>> field = Field.from_dsl('int, unique')
>>> field.unique
True

.. _add-custom-by-options:

Adding Custom By-Options
------------------------

Use :meth:`~sphinxnotes.render.data.Registry.add_by_option` method of
:data:`sphinxnotes.render.REGISTRY` to add a new by-option:

>>> from sphinxnotes.render import REGISTRY
>>> REGISTRY.data.add_by_option('group', str)
>>> field = Field.from_dsl('str, group by size')
>>> field.group
'size'
>>> REGISTRY.data.add_by_option('index', str, store='append')
>>> field = Field.from_dsl('str, index by month, index by year')
>>> field.index
['month', 'year']
