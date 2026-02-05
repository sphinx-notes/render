"""
sphinxnotes.data.render.sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This module provides helpful BaseContextSource subclasses.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override
from abc import abstractmethod

from docutils.parsers.rst import directives

from ..data import Field, RawData, Schema
from .ctx import Context, UnparsedData, PENDING_CONTEXT_STORAGE
from .render import Template
from .pipeline import BaseContextSource, BaseContextDirective, BaseContextRole

if TYPE_CHECKING:
    pass


class BaseRawDataSource(BaseContextSource):
    """
    A BaseContextRenderer subclass, which itself is a definition of raw data.
    """

    """Methods to be implemented."""

    @abstractmethod
    def current_raw_data(self) -> RawData: ...

    @abstractmethod
    def current_schema(self) -> Schema: ...

    """Methods to be overrided."""

    @override
    def current_context(self) -> Context:
        data = UnparsedData(self.current_raw_data(), self.current_schema())
        ref = PENDING_CONTEXT_STORAGE.stash(data)
        return ref


class BaseDataDefineDirective(BaseRawDataSource, BaseContextDirective):
    @override
    def current_raw_data(self) -> RawData:
        return RawData(
            ' '.join(self.arguments) if self.arguments else None,
            self.options.copy(),
            '\n'.join(self.content) if self.has_content else None,
        )


class BaseDataDefineRole(BaseRawDataSource, BaseContextRole):
    @override
    def current_raw_data(self) -> RawData:
        return RawData(self.name, self.options.copy(), self.text)


class StrictDataDefineDirective(BaseDataDefineDirective):
    final_argument_whitespace = True

    schema: Schema
    template: Template

    @override
    def current_template(self) -> Template:
        return self.template

    @override
    def current_schema(self) -> Schema:
        return self.schema

    @classmethod
    def derive(
        cls, name: str, schema: Schema, tmpl: Template
    ) -> type[StrictDataDefineDirective]:
        if not schema.name:
            required_arguments = 0
            optional_arguments = 0
        elif schema.name.required:
            required_arguments = 1
            optional_arguments = 0
        else:
            required_arguments = 0
            optional_arguments = 1

        assert not isinstance(schema.attrs, Field)
        option_spec = {}
        for name, field in schema.attrs.items():
            if field.required:
                option_spec[name] = directives.unchanged_required
            else:
                option_spec[name] = directives.unchanged

        has_content = schema.content is not None

        # Generate directive class
        return type(
            'Strict%sDataDefineDirective' % name.title(),
            (cls,),
            {
                'schema': schema,
                'template': tmpl,
                'has_content': has_content,
                'required_arguments': required_arguments,
                'optional_arguments': optional_arguments,
                'option_spec': option_spec,
            },
        )
