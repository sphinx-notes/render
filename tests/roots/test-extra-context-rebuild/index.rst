Extra Context Rebuild Test
==========================

.. data.render::
   :on: resolving

   {% set doc = load_extra('doc') %}
   {% set env = load_extra('env') %}

   doc-sections={{ doc.sections | length }}
   all-docs={{ env.all_docs | length }}
