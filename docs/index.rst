.. This file is generated from sphinx-notes/cookiecutter.
   You need to consider modifying the TEMPLATE or modifying THIS FILE.

==================
sphinxnotes-render
==================

.. |docs| image:: https://img.shields.io/github/deployments/sphinx-notes/render/github-pages?label=docs
   :target: https://sphinx.silverrainz.me/render
   :alt: Documentation Status
.. |license| image:: https://img.shields.io/github/license/sphinx-notes/render
   :target: https://github.com/sphinx-notes/data/blob/master/LICENSE
   :alt: Open Source License
.. |pypi| image:: https://img.shields.io/pypi/v/sphinxnotes-render.svg
   :target: https://pypistats.org/packages/sphinxnotes-render
   :alt: PyPI Package
.. |download| image:: https://img.shields.io/pypi/dm/sphinxnotes-render
   :target: https://pypi.python.org/pypi/sphinxnotes-render
   :alt: PyPI Package Downloads
.. |github| image:: https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white/
   :target: https://github.com/sphinx-notes/render
   :alt: GitHub Repository

|docs| |license| |pypi| |download| |github|

Introduction
============

.. INTRODUCTION START

This extension mainly consists of two parts:

:parsed_literal:`:ref:\`sphinxnotes.render.ext <extension>\``
   An extension built on top of this framework, allowing user to
   :rst:dir:`define <data.define>`, :rst:dir:`constrain <data.schema>` and
   :rst:dir:`render <data.template>` data entirely through the markup language.

:parsed_literal:`:ref:\`sphinxnotes.render <framework>\``
   A framework to define, constrain, and render data in Sphinx documentation.

.. INTRODUCTION END

Getting Started
===============

.. note::

   In this section we discuss how to use the ``sphinxnotes.render.ext``
   extension. For the document to write your own extension, please refer to
   :doc:`ext`.

.. note::

   We assume you already have a Sphinx documentation,
   if not, see `Getting Started with Sphinx`_.


First, downloading extension from PyPI:

.. code-block:: console

   $ pip install "sphinxnotes-render[ext]"


Then, add the extension name to ``extensions`` configuration item in your
:parsed_literal:`conf.py_`:

.. code-block:: python

   extensions = [
             # …
             'sphinxnotes.render.ext',
             # …
             ]

.. _Getting Started with Sphinx: https://www.sphinx-doc.org/en/master/usage/quickstart.html
.. _conf.py: https://www.sphinx-doc.org/en/master/usage/configuration.html

.. ADDITIONAL CONTENT START

We need to create a template to tell extension how to render the data.
The extension provides two ways for this:

Way 1: by Directive
-------------------

The :rst:dir:`data.template` directive will not change the content document,
it creates and stashes a temporary template for later use:

.. code:: rst

   .. data.template::

      Hi human! I am a cat named {{ name }}, I have {{ color }} fur.

      {{ content }}.

.. data.template::

   Hi human! I am a cat named {{ name }}, I have {{ color }} fur.

   {{ content }}.

Now we can define data now, using a :rst:dir:`data.define` directive:

.. example::
   :style: grid

   .. data.define:: mimi
      :color: black and brown

      I like fish!

Please refer to :ref:`ext-usage-directives` for more details.

Way 2: by Configuration
-----------------------

Add the following code to your :file:`conf.py`:

.. literalinclude:: conf.py
   :language: python
   :start-after: [example config start]
   :end-before: [example config end]

This creates a ``.. cat::`` directive that requires a name argument and accepts
a ``color`` options and a content block. Use it in your document:

.. example::
   :style: grid

   .. cat:: mimi
      :color: black and brown

      I like fish!

Please refer to :confval:`data_define_directives` for more details.

.. ADDITIONAL CONTENT END

Contents
========

.. toctree::
   :caption: Contents

   changelog

.. toctree::
   :name: extension
   :caption: Extension
   :maxdepth: 1

   usage
   conf

.. toctree::
   :name: framework
   :caption: Framework
   :maxdepth: 1

   tmpl
   ext
   dsl
   api

The Sphinx Notes Project
========================

The project is developed by `Shengyu Zhang`__,
as part of **The Sphinx Notes Project**.

.. toctree::
   :caption: The Sphinx Notes Project

   Home <https://sphinx.silverrainz.me/>
   GitHub <https://github.com/sphinx-notes>
   Blog <https://silverrainz.me/blog/category/sphinx.html>
   PyPI <https://pypi.org/search/?q=sphinxnotes>

__ https://github.com/SilverRainZ
