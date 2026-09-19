#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Define the interface-independent interactive collection API.

The collection layer is deliberately separate from :class:`upref.ConfigStore`:
asking for values never reads or writes a configuration file. Terminal and GUI
implementations are imported only when selected, so importing :mod:`upref` has
no optional UI dependencies or user-interface side effects.

Collection is driven by immutable :class:`Field` definitions. Raw strings
returned by a :class:`Prompter` are parsed, validated, and normalized to the
Upref configuration data model before they enter the result. Conversion or
validation failures are shown through the prompter and retried; cancellation is
reported by raising :class:`upref.errors.PromptCancelled`.

The ``secret`` flag is only a presentation hint for prompters. The bundled
interfaces request non-echoing or password-style entry and avoid displaying an
existing value, but terminal capabilities and custom implementations determine
the actual presentation. The returned value remains plaintext in memory and is
not encrypted if the caller later persists it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Literal, Protocol, cast, runtime_checkable

from ._types import Config, ConfigValue, normalize_config
from .errors import PromptCancelled

Parser = Callable[[str], ConfigValue]
Validator = Callable[[ConfigValue], bool | None]
PromptMode = Literal["missing", "all"]


def parse_bool(raw: str) -> bool:
    """Parse yes/no, true/false, on/off, or 1/0, ignoring case and whitespace.

    Unlike ``bool(text)``, this function interprets the text's meaning.
    Single-letter ``y`` and ``n`` are also accepted.

    Args:
        raw: Text supplied by a prompter or environment variable.

    Returns:
        The boolean represented by the input.

    Raises:
        ValueError: If the text is not a recognized boolean spelling.
    """
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError("Enter yes/no, true/false, on/off, or 1/0")


@dataclass(frozen=True, slots=True)
class Field:
    """Describe the presentation and conversion rules for one value.

    Fields are immutable and can therefore be reused safely across collection
    calls. The parser receives the raw string returned by the prompter. The
    validator then receives the parsed value and may either return ``False`` or
    raise :class:`ValueError` to reject it. A return value of ``True`` or
    ``None`` accepts the value.

    ``secret`` does not make a value safe to persist. It asks a compatible
    prompter to mask input and suppress the current value; custom prompters are
    responsible for honoring that hint. Parsed secret values remain plaintext.

    Attributes:
        label: Human-readable field name. Bundled prompters fall back to the
            schema key when this string is empty.
        description: Optional explanatory text displayed before entry.
        required: Whether an empty raw answer is rejected. In ``"missing"``
            mode, this also makes an existing empty string count as missing.
        secret: Whether compatible prompters should mask entry and hide the
            current value. This is a display-only safeguard, not encryption.
        parser: Callable converting raw input to a supported configuration
            value. Raising :class:`ValueError` displays the error and retries;
            secret fields use a generic message instead of the exception text.
        validator: Optional callable checking the parsed value. Returning
            ``False`` or raising :class:`ValueError` rejects the value and
            retries the prompt.
        formatter: Keyword-only callable converting an existing value into
            text understood by ``parser``. Used by bundled interfaces for
            display, GUI prefill, and optional terminal value reuse. Defaults
            to :class:`str`; use e.g. ``json.dumps`` with ``json.loads``.
    """

    label: str
    description: str = ""
    required: bool = True
    secret: bool = False
    parser: Parser = str
    validator: Validator | None = None
    formatter: Callable[[ConfigValue], str] = dataclass_field(default=str, kw_only=True)

    def __post_init__(self) -> None:
        """Reject malformed field definitions before opening an interface."""
        for name in ("label", "description"):
            if not isinstance(getattr(self, name), str):
                raise TypeError(f"Field.{name} must be a string")
        for name in ("required", "secret"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"Field.{name} must be a boolean")
        for name in ("parser", "formatter"):
            if not callable(getattr(self, name)):
                raise TypeError(f"Field.{name} must be callable")
        if self.validator is not None and not callable(self.validator):
            raise TypeError("Field.validator must be callable or None")


@runtime_checkable
class Prompter(Protocol):
    """Specify the minimal interface for an interactive front end.

    Runtime-checkable implementations supply raw input and display recoverable
    parsing or validation errors. Returning ``None`` from :meth:`ask` signals
    cancellation; an empty string is an entered value and is handled according
    to :attr:`Field.required`.

    A custom implementation may expose a ``close()`` method, but
    :func:`collect` does not call it because the caller owns custom prompters.
    """

    def ask(
        self,
        name: str,
        field: Field,
        current: ConfigValue,
    ) -> str | None:
        """Request one raw value from the user.

        Args:
            name: Configuration key being collected.
            field: Presentation and conversion metadata for the key.
            current: Existing value, or ``None`` when no value is available.
                Implementations should not reveal it when ``field.secret`` is
                true.

        Returns:
            The unparsed text entered by the user, including an empty string,
            or ``None`` to signal cancellation.
        """
        ...

    def show_error(self, message: str) -> None:
        """Display a recoverable conversion or validation error.

        Args:
            message: Human-readable explanation of why the value was rejected.

        Returns:
            None.
        """
        ...


def _validate_interface(
    interface: object,
) -> Literal["tty", "gui"] | Prompter:
    """Validate and narrow an interface value without creating a UI.

    Args:
        interface: Candidate bundled selector or custom prompter.

    Returns:
        The validated selector or caller-owned prompter.

    Raises:
        TypeError: If a non-string value does not implement :class:`Prompter`.
        ValueError: If a string is neither ``"tty"`` nor ``"gui"``.
    """
    if isinstance(interface, str):
        if interface == "tty":
            return "tty"
        if interface == "gui":
            return "gui"
        raise ValueError("interface must be 'tty' or 'gui'")
    if not isinstance(interface, Prompter) or not all(
        callable(getattr(interface, name)) for name in ("ask", "show_error")
    ):
        raise TypeError(
            "interface must be 'tty', 'gui', or an object implementing "
            "the Prompter protocol"
        )
    return interface


def _validated_schema_items(
    schema: Mapping[str, Field],
) -> list[tuple[str, Field]]:
    """Validate schema entries at runtime and return typed items.

    Args:
        schema: Candidate mapping from field names to definitions.

    Returns:
        Schema items in their original iteration order.

    Raises:
        TypeError: If a key is not a string or a value is not a :class:`Field`.
    """
    if not isinstance(schema, Mapping):
        raise TypeError("schema must be a mapping")
    raw_schema = cast(Mapping[object, object], schema)
    items: list[tuple[str, Field]] = []
    for name, field in raw_schema.items():
        if not isinstance(name, str):
            raise TypeError("schema keys must be strings")
        if not isinstance(field, Field):
            raise TypeError(f"schema entry {name!r} must be a Field")
        items.append((name, field))
    return items


def _make_prompter(interface: str | Prompter) -> tuple[Prompter, bool]:
    """Resolve an interface selector to a prompter instance.

    Bundled interfaces are imported lazily. A caller-provided implementation is
    returned unchanged and remains owned by the caller.

    Args:
        interface: ``"tty"``, ``"gui"``, or an object satisfying
            :class:`Prompter`.

    Returns:
        A pair containing the resolved prompter and a flag that is ``True``
        when this function created the instance. The flag tells
        :func:`collect` whether it is responsible for closing the prompter.

    Raises:
        TypeError: If a non-string object does not implement :class:`Prompter`.
        ValueError: If a string is neither ``"tty"`` nor ``"gui"``.
        upref.errors.PromptUnavailableError: If the GUI implementation is
            selected but wxPython cannot be imported or initialized.
    """
    validated = _validate_interface(interface)
    if not isinstance(validated, str):
        return validated, False

    if validated == "tty":
        from .tty import TTYPrompter

        return TTYPrompter(), True
    from .gui import GuiPrompter

    return GuiPrompter(), True


def _is_missing(present: bool, value: ConfigValue, field: Field) -> bool:
    """Determine whether a field needs input in ``"missing"`` mode.

    Args:
        present: Whether the configuration mapping contains the field key.
        value: Current value for the field, or ``None`` when absent or
            explicitly unset.
        field: Field definition controlling whether an empty string is
            considered missing.

    Returns:
        ``True`` when the key is absent, the value is ``None``, or the field is
        required and its current value is an empty string. Values such as
        ``False``, ``0``, and an optional empty string are not missing.
    """
    if not present or value is None:
        return True
    return field.required and value == ""


def _parse_value(
    prompter: Prompter,
    name: str,
    field: Field,
    current: ConfigValue,
) -> ConfigValue:
    """Prompt repeatedly until one field produces an acceptable value.

    Required empty input is rejected before parsing. A :class:`ValueError`
    raised by the parser or validator causes another attempt, as does a
    validator result of ``False``. Its text is displayed for ordinary fields;
    secret fields receive a generic error to avoid echoing input. Accepted
    parser output is normalized to detach mutable values and reject types
    outside the Upref data model.

    Args:
        prompter: Front end used to request input and report recoverable errors.
        name: Configuration key being collected.
        field: Presentation, parsing, and validation rules for the key.
        current: Existing value passed to the prompter as context.

    Returns:
        The parsed, validated, and detached configuration value.

    Raises:
        PromptCancelled: If the prompter returns ``None``.
        upref.errors.ConfigFormatError: If the parser returns an unsupported
            value or a cyclic container.
        Exception: Exceptions from the prompter, parser, or validator other
            than parser/validator :class:`ValueError` propagate unchanged.
    """
    while True:
        raw = prompter.ask(name, field, current)
        if raw is None:
            raise PromptCancelled(f"Input cancelled while asking for {name!r}")
        if not isinstance(raw, str):
            raise TypeError("Prompter.ask() must return a string or None")

        if field.required and raw == "":
            prompter.show_error(f"{field.label or name} is required")
            continue

        try:
            value = field.parser(raw)
            if field.validator is not None:
                valid = field.validator(value)
                if valid is False:
                    raise ValueError(f"Invalid value for {field.label or name}")
        except ValueError as error:
            message = (
                f"Invalid value for {field.label or name}"
                if field.secret
                else str(error) or f"Invalid value for {name}"
            )
            prompter.show_error(message)
            continue

        # Validate and detach a parser result before it joins the output.  This
        # also prevents a custom parser from smuggling unsupported YAML types
        # into a value advertised as ConfigValue.
        return normalize_config({name: value})[name]


def collect(
    schema: Mapping[str, Field],
    initial: Mapping[str, ConfigValue] | None = None,
    interface: str | Prompter = "tty",
    mode: PromptMode = "missing",
) -> Config:
    """Collect configuration values without mutating or persisting inputs.

    In ``"missing"`` mode, a field is requested when its key is absent, its
    value is ``None``, or a required string is empty.  Values such as ``False``
    and ``0`` are therefore already populated.  ``"all"`` requests every
    field. Keys in ``initial`` that are not part of ``schema`` are preserved.
    Schema iteration order determines prompt order.

    ``initial`` is normalized into a detached tree before collection, and
    parser results are normalized before insertion. Consequently, neither the
    input mapping nor nested mutable objects returned by a parser are shared
    with the result. Collection has no persistence side effects: callers must
    explicitly pass the returned mapping to a store.

    String selectors create bundled prompters lazily. If a created prompter
    exposes ``close()``, it is called in a ``finally`` block, including after
    cancellation or another error. A caller-provided prompter is never closed
    by this function. If no fields require input, a selected bundled interface
    is not instantiated.

    Args:
        schema: Mapping from configuration keys to immutable field
            definitions.
        initial: Existing configuration values. Unsupported values, non-string
            keys, and cyclic containers are rejected. Defaults to an empty
            mapping.
        interface: ``"tty"`` for dependency-free terminal input, ``"gui"``
            for optional wxPython dialogs, or a caller-owned :class:`Prompter`.
        mode: ``"missing"`` to request only absent or incomplete fields, or
            ``"all"`` to request every schema field.

    Returns:
        A new, detached configuration dictionary containing preserved initial
        keys and all successfully collected values.

    Raises:
        TypeError: If schema is not a mapping, schema keys are not strings, values are not
            :class:`Field` instances, or a non-string ``interface`` does not
            implement :class:`Prompter` with callable methods, or ``ask``
            returns neither text nor ``None``.
        ValueError: If ``mode`` or a string ``interface`` selector is invalid.
        PromptCancelled: If the user cancels any requested field. Partial
            results are discarded and ``initial`` remains unchanged.
        upref.errors.ConfigFormatError: If ``initial`` or a parser result lies
            outside the supported configuration data model.
        upref.errors.PromptUnavailableError: If the GUI interface is requested
            but wxPython cannot be imported or initialized.
        Exception: Unexpected exceptions from a prompter, parser, validator,
            or owned prompter's ``close()`` method propagate. A close failure
            during exception handling can replace the original exception.
    """
    if mode not in ("missing", "all"):
        raise ValueError("mode must be 'missing' or 'all'")

    validated_interface = _validate_interface(interface)
    schema_items = _validated_schema_items(schema)

    values = normalize_config({} if initial is None else initial)
    fields_to_ask = [
        (name, field)
        for name, field in schema_items
        if mode == "all" or _is_missing(name in values, values.get(name), field)
    ]
    if not fields_to_ask:
        return values

    prompter, owned = _make_prompter(validated_interface)

    try:
        for name, field in fields_to_ask:
            current = values.get(name)
            values[name] = _parse_value(prompter, name, field, current)
        return values
    finally:
        if owned:
            close = getattr(prompter, "close", None)
            if close is not None:
                close()


__all__ = ["Field", "Prompter", "PromptMode", "collect", "parse_bool"]
