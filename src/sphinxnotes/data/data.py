from __future__ import annotations
import re
import dataclasses
from typing import Any, Callable


type Value = None | int | float | str | bool | list[Value]


@dataclasses.dataclass(frozen=True)
class Raw(object):
    name: str | None
    attrs: dict[str, str]
    content: str


@dataclasses.dataclass(frozen=True)
class Data(object):
    name: Value
    attrs: dict[str, Value]
    content: Value

    @staticmethod
    def from_raw(raw: Raw) -> Data:
        return Data(
            name=raw.name,
            attrs={k: v for k, v in raw.attrs.items()},
            content=raw.content,
        )

    def ascontext(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class Form:
    """Defines how to split the string and the return type."""

    rtype: type
    sep: str


class Registry:
    """Stores supported element types and element forms (containers)."""

    etypes: dict[str, type] = {
        'bool': bool,
        'flag': bool,
        'int': int,
        'integer': int,
        'float': float,
        'number': float,
        'str': str,
        'string': str,
    }

    @staticmethod
    def _bool_conv(v: str | None) -> bool:
        v = v.lower().strip() if v is not None else None
        if v in ('true', 'yes', '1', 'on', 'y', ''):
            return True
        if v in ('false', 'no', '0', 'off', 'n', None):
            return False
        # Same to :meth:`directives.flag`.
        raise ValueError(f'no argument is allowed; "{v}" supplied')

    convs: dict[type, Callable[[str], Any]] = {
        bool: _bool_conv,
        int: int,
        float: float,
        str: str,
    }

    forms: dict[str, Form] = {
        'list': Form(rtype=list, sep=','),
        'lines': Form(rtype=list, sep='\n'),
        'words': Form(
            rtype=list,
            sep=' ',
        ),
    }


@dataclasses.dataclass()
class Field:
    # Type of element.
    etype: type = str
    required: bool = False
    # Form of elements (if the field holds multiple values).
    form: Form | None = None

    @staticmethod
    def from_str(dsl: str) -> Field:
        """Parses the DSL string into a Field object."""
        self = Field()
        # Initialize form as None, implied scalar unless modifiers change it.
        for mod in self._split_modifiers(dsl):
            if mod.strip():
                self._apply_modifier(mod.strip())
        return self

    def _split_modifiers(self, text: str) -> list[str]:
        """Splits the DSL string by comma, ignoring commas inside quotes."""
        parts, current, quote_char = [], [], None

        for ch in text:
            if quote_char:
                current.append(ch)
                if ch == quote_char:
                    quote_char = None
            else:
                if ch in ('"', "'"):
                    quote_char = ch
                    current.append(ch)
                elif ch == ',':
                    parts.append(''.join(current))
                    current = []
                else:
                    current.append(ch)

        if current:
            parts.append(''.join(current))

        return parts

    def _apply_modifier(self, mod: str):
        clean_mod = mod.strip()
        lower_mod = clean_mod.lower()

        # Match: XXX of XXX (e.g., "list of int")
        if match := re.match(r'^([a-zA-Z_]+)\s+of\s+([a-zA-Z_]+)$', lower_mod):
            form, etype = match.groups()

            if etype not in Registry.etypes:
                raise ValueError(
                    f'unsupported type: "{etype}". '
                    f'available: {list(Registry.etypes.keys())}'
                )
            if form not in Registry.forms:
                raise ValueError(
                    f'unsupported form: "{form}". '
                    f'available: {list(Registry.forms.keys())}'
                )
            self.etype = Registry.etypes[etype]
            if self.form is None:
                self.form = Registry.forms[form]
            else:
                # Create a copy so we don't mutate the global registry default
                # when modifying self.form.sep later.
                self.form = Form(Registry.forms[form].rtype, self.form.sep)
            return

        # Match: Type only (e.g., "int")
        if lower_mod in Registry.etypes:
            self.etype = Registry.etypes[lower_mod]
            return

        # Match: Required flag
        if lower_mod in ['required', 'req']:
            self.required = True
            return

        # Match: Custom separator (e.g., "sep by '|'")
        if match := re.match(r'^sep\s+by\s+(.+)$', clean_mod, re.IGNORECASE):
            rawsep = match.group(1).strip()
            # Default to list if 'sep by' is used without a 'xxx of xxx'.
            form = self.form or Registry.forms['list']
            self.form = Form(form.rtype, self._strip_quotes(rawsep))
            return

        raise ValueError(f"unknown modifier: '{mod}'")

    def _strip_quotes(self, s: str) -> str:
        """Removes outer quotes and unescapes basic characters."""
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
            content = s[1:-1]
            return content.replace(r'\n', '\n').replace(r'\t', '\t').replace(r'\,', ',')
        return s

    def parse(self, rawval: str | None) -> Value:
        """
        Parses the raw input string into the target Value.
        When a None is passed, which means the field is not supplied.
        """
        if rawval is None:
            if self.required:
                # Same to :meth:`directives.unchanged_required`.
                raise ValueError('argument required but none supplied')
            if self.form:
                # Return a empty container when a None value is optional.
                return self.form.rtype()
            if self.etype is bool:
                # Special case: A single bool field is valid even when
                # value is not supplied.
                return Registry._bool_conv(rawval)
            return None

        # Strip whitespace. TODO: supported unchanged?
        rawval = rawval.strip()

        try:
            conv = Registry.convs[self.etype]

            if self.form is None:
                # Parse as scalar
                return conv(rawval)

            # Parse as container
            if self.form.sep == ' ':
                items = rawval.split()  # split by arbitrary whitespace
            elif self.form.sep == '':
                items = list(rawval)  # split by char
            else:
                items = rawval.split(self.form.sep)

            elems = [conv(x.strip()) for x in items if x.strip() != '']

            return self.form.rtype(elems)
        except ValueError as e:
            raise ValueError(f"failed to parse '{rawval}' as {self.etype}: {e}")


def assert_no_arg_allowed(arg: str) -> None:
    raise ValueError(f'no argument is allowed; "{arg}" supplied')


@dataclasses.dataclass(frozen=True)
class Schema(object):
    name: Field | None
    attrs: dict[str, Field]
    content: Field | None

    def _parse_single(
        self, field: tuple[str, Field | None], rawval: str | None
    ) -> Value:
        if field[1] is None and rawval is not None:
            raise ValueError(
                f'parsing {field[0]}: no argument is allowed; "{rawval}" supplied'
            )

        try:
            assert field[1] is not None
            return field[1].parse(rawval)
        except Exception as e:
            raise ValueError(f'parsing {field[0]}: {e}')

    def parse(self, raw: Raw) -> Data:
        name = self._parse_single(('name', self.name), raw.name)

        attrs = {}
        rawattrs = raw.attrs.copy()
        for key, field in self.attrs.items():
            rawval = rawattrs.pop(key)
            attrs[key] = self._parse_single(('attrs.' + key, field), rawval)
        for key, rawval in rawattrs.items():
            raise ValueError(f'unknown attr: "{key}"')

        content = self._parse_single(('content', self.name), raw.content)

        return Data(name, attrs, content)
