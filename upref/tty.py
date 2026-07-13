"""Provide the dependency-free terminal prompt implementation.

:class:`TTYPrompter` writes field context to a configurable output function and
reads raw text through :func:`input` or :func:`getpass.getpass`. End-of-file and
keyboard interruption are translated to the protocol's cancellation sentinel,
``None``; :func:`upref.prompt.collect` then raises
:class:`upref.errors.PromptCancelled`.

Secret entry delegates to ``getpass`` and suppresses display of the current
value. Non-echoing input depends on terminal support; the standard library can
warn and fall back to echoed input. The raw secret is returned as plaintext and
is not encrypted in memory or at rest.
"""

from __future__ import annotations

import builtins
import getpass
from collections.abc import Callable

from ._types import ConfigValue
from .prompt import Field

ReadFunction = Callable[[str], str]
PrintFunction = Callable[[str], object]


class TTYPrompter:
    """Ask for fields using standard terminal input.

    The three functions are injectable so applications and tests can control
    input and presentation without replacing process-wide builtins. This
    prompter owns no external resource and requires no explicit close step.
    """

    def __init__(
        self,
        input_func: ReadFunction | None = None,
        getpass_func: ReadFunction | None = None,
        print_func: PrintFunction | None = None,
    ) -> None:
        """Initialize a terminal prompter.

        Args:
            input_func: Reader for ordinary fields. It receives the prompt text
                and returns one raw line. Defaults to :func:`input`.
            getpass_func: Reader for secret fields. It receives the prompt text
                and should avoid echoing entered characters. Defaults to
                :func:`getpass.getpass`.
            print_func: Function used to display labels, descriptions, current
                values, and errors. Defaults to :func:`print`.

        Returns:
            None.
        """
        self._input = builtins.input if input_func is None else input_func
        self._getpass = getpass.getpass if getpass_func is None else getpass_func
        self._print = builtins.print if print_func is None else print_func

    def ask(
        self,
        name: str,
        field: Field,
        current: ConfigValue,
    ) -> str | None:
        """Display field context and read one raw line.

        The field label and optional description are displayed first. A
        non-``None`` current value is also displayed for ordinary fields.
        Secret fields instead use the injected password reader and never show
        the current value. The returned secret is nevertheless plaintext.

        Args:
            name: Configuration key, used as the label when ``field.label`` is
                empty.
            field: Presentation metadata, including whether entry is secret.
            current: Existing value to display for an ordinary field, or
                ``None`` when unavailable.

        Returns:
            The raw line returned by the selected reader, including an empty
            string, or ``None`` when reading raises :class:`EOFError` or
            :class:`KeyboardInterrupt`.

        Raises:
            Exception: Display-function errors and reader errors other than
                :class:`EOFError` and :class:`KeyboardInterrupt` propagate.
                The two cancellation exceptions are converted only when the
                selected reader raises them.
        """
        self._print(field.label or name)
        if field.description:
            self._print(field.description)
        if current is not None and not field.secret:
            self._print(f"Current value: {current}")

        reader = self._getpass if field.secret else self._input
        try:
            return reader("> ")
        except (EOFError, KeyboardInterrupt):
            return None

    def show_error(self, message: str) -> None:
        """Display a conversion or validation error with a clear prefix.

        Args:
            message: Human-readable error supplied by the collection layer.

        Returns:
            None.

        Raises:
            Exception: Any exception from the injected output function
                propagates unchanged.
        """
        self._print(f"Error: {message}")


__all__ = ["TTYPrompter"]
