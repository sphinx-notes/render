=============
Configuration
=============

The extension provides the following configuration:

.. autoconfval:: data_define_directives

   A dictionary ``dict[str, directive_def]`` for creating custom directives for
   data definition.

   The ``str`` key is the name of the directive to be created;
   The ``directive_def`` value is a ``dict`` with the following keys:

   - ``schema`` (dict): Schema definition, works same as the
     :rst:dir:`data.schema` directive, which has the following keys:

     - ``name`` (str, optional): same as the directive argument
     - ``attr`` (dict, can be empty): same as the directive options
     - ``content`` (str, optional): same as the directive content

   - ``template`` (dict): Template definition, works same as the
     :rst:dir:`data.template` directive, which has the following keys:

     - ``text`` (str): the Jinja2 template text.
     - ``on`` (str, optional): same as :rst:dir:`data.template:on`
     - ``debug`` (bool, optional): same as :rst:dir:`data.template:debug`

   See :ref:`custom-dir` for example.

