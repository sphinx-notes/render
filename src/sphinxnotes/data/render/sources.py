"""
sphinxnotes.data.render.sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.

This module provides helpful BaseDataSource subclasses.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, override
from abc import abstractmethod

from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import directive

from ..data import Field, RawData, PendingData, ParsedData, Schema
from .render import Template
from .pipeline import BaseDataSource, BaseDataDirective, BaseDataRole

if TYPE_CHECKING:
    from typing import Any

class BaseRawDataSource(BaseDataSource):
    """
    A BaseDataRenderer subclass, which itself is a definition of raw data
    """

    """Methods to be implemented."""

    @abstractmethod
    def current_raw_data(self) -> RawData: ...

    @abstractmethod
    def current_schema(self) -> Schema: ...

    """Methods to be overrided."""

    @override
    def current_data(self) -> PendingData | ParsedData | dict[str, Any]:
        return PendingData(self.current_raw_data(), self.current_schema())


class BaseDataDefineDirective(BaseRawDataSource, BaseDataDirective):
    @override
    def current_raw_data(self) -> RawData:
        return RawData(
            ' '.join(self.arguments) if self.arguments else None,
            self.options.copy(),
            '\n'.join(self.content) if self.has_content else None,
        )


class BaseDataDefineRole(BaseRawDataSource, BaseDataRole):
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
            '%sStrictDataDefineDirective' % name.title(),
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
