#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Provide the optional wxPython prompt implementation.

Importing this module does not import wxPython. The optional dependency is
loaded only when :class:`GuiPrompter` is instantiated. A prompter reuses the
active wx application when one exists; otherwise it creates a private
``wx.App`` and destroys only that application when closed.

Secret dialogs use wxPython's password-entry style and are never prefilled with
the current value. This prevents ordinary visual disclosure, not access to the
plaintext returned by the dialog, and provides no encryption for subsequent
persistence.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

from ._types import ConfigValue
from .errors import PromptUnavailableError

if TYPE_CHECKING:
    from .prompt import Field


class GuiPrompter:
    """Collect one value at a time with wxPython modal dialogs.

    Instances can be closed explicitly or used as context managers. Closing is
    idempotent and destroys a ``wx.App`` only when this instance created it.
    An application that already existed at construction remains owned by its
    original caller. Once closed, the prompter cannot display new dialogs.
    """

    def __init__(self, title: str = "Preferences", parent: Any = None) -> None:
        """Initialize wxPython and prepare a modal-dialog prompter.

        Args:
            title: Window title used by text-entry and error dialogs.
            parent: Optional wx window that owns the dialogs. ``None`` creates
                top-level dialogs according to wxPython's normal behavior.

        Returns:
            None.

        Raises:
            PromptUnavailableError: If wxPython is not installed or a wx
                application cannot be initialized.
        """
        try:
            wx = import_module("wx")
        except Exception as error:
            raise PromptUnavailableError(
                "wxPython could not be imported; install or repair the 'gui' extra"
            ) from error

        self._wx: ModuleType = wx
        self._parent = parent
        self._app: Any = None
        self._closed = False
        self.title = title

        try:
            get_app = getattr(wx, "GetApp", None)
            existing_app = get_app() if get_app is not None else None
            if existing_app is None:
                self._app = wx.App(False)
        except Exception as error:
            raise PromptUnavailableError(
                "wxPython is installed but its GUI could not be initialized"
            ) from error

    def ask(
        self,
        name: str,
        field: Field,
        current: ConfigValue,
    ) -> str | None:
        """Show a modal text-entry dialog for one field.

        Ordinary fields are prefilled with a non-``None`` current value.
        Secret fields use wxPython's password style and deliberately start
        empty, so the current secret is neither displayed nor copied into the
        widget. Any entered secret is still returned as plaintext. The dialog
        is destroyed after confirmation or cancellation and when displaying or
        reading the constructed dialog raises an error.

        Args:
            name: Configuration key, used as the label when ``field.label`` is
                empty.
            field: Presentation metadata, including description and secret
                handling.
            current: Existing value used as the default for an ordinary field,
                or ``None`` when unavailable.

        Returns:
            The raw dialog text when the user confirms, including an empty
            string, or ``None`` when the dialog is cancelled or dismissed.

        Raises:
            RuntimeError: If the prompter has already been closed.
            Exception: Errors raised by wxPython while constructing, showing,
                reading, or destroying the dialog propagate unchanged.
        """
        if self._closed:
            raise RuntimeError("GuiPrompter is closed")

        wx = self._wx
        label = field.label or name
        message = label
        if field.description:
            message = f"{label}\n\n{field.description}"

        default_value = ""
        if current is not None and not field.secret:
            default_value = str(current)

        style = wx.OK | wx.CANCEL
        if field.secret:
            style |= wx.TE_PASSWORD

        dialog = wx.TextEntryDialog(
            self._parent,
            message,
            self.title,
            default_value,
            style,
        )
        try:
            if dialog.ShowModal() == wx.ID_OK:
                return str(dialog.GetValue())
            return None
        finally:
            dialog.Destroy()

    def show_error(self, message: str) -> None:
        """Display a modal conversion or validation error.

        Args:
            message: Human-readable error supplied by the collection layer.

        Returns:
            None.

        Raises:
            RuntimeError: If the prompter has already been closed.
            Exception: Errors raised by ``wx.MessageBox`` propagate unchanged.
        """
        if self._closed:
            raise RuntimeError("GuiPrompter is closed")
        wx = self._wx
        wx.MessageBox(
            message,
            self.title,
            wx.OK | wx.ICON_ERROR,
            self._parent,
        )

    def close(self) -> None:
        """Release GUI resources owned by this prompter.

        Closing is idempotent. If construction created a private ``wx.App``,
        its ``Destroy`` method is called when available. An application that
        predated this prompter is never destroyed.

        Returns:
            None.

        Raises:
            Exception: An error raised by the owned ``wx.App.Destroy`` method
                propagates. The prompter remains marked as closed.
        """
        if self._closed:
            return
        self._closed = True
        if self._app is not None:
            destroy = getattr(self._app, "Destroy", None)
            if destroy is not None:
                destroy()
            self._app = None

    def __enter__(self) -> GuiPrompter:
        """Enter a context manager without changing GUI ownership.

        Entering does not initialize another application or reopen a prompter
        that was already closed.

        Returns:
            This prompter instance.
        """
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the prompter when leaving a context manager.

        Args:
            *exc_info: Exception details supplied by the context-management
                protocol. They are not inspected or suppressed.

        Returns:
            None. An exception from the managed block normally propagates.

        Raises:
            Exception: An exception from :meth:`close` propagates and can
                replace an active exception from the managed block.
        """
        self.close()


__all__ = ["GuiPrompter"]
