Smoke Test
==========

.. data.template::

   Rendered{{ name }}

   {% for k, v in attrs.items() %}
   Rendered{{ k }}: Rendered{{ v }}
   {% endfor %}

   Rendered{{ content }}

.. data.define:: Name
   :Attr1: Value1
   :Attr2: Value2

   Content
