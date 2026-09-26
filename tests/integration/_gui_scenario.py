"""Exercise real modal dialogs inside a disposable wxPython process."""

import json
import sys
from unittest.mock import patch

import wx

from upref import Field, PromptCancelled, collect
from upref.gui import GuiPrompter


def ask_with_response(
    prompter, field, current, *, entered, result, expected_text, secret=False
):
    """Inspect native prefill and input style, then finish the modal dialog."""
    errors = []

    def respond():
        """Close the native dialog even when an assertion fails."""
        dialogs = [
            window
            for window in wx.GetTopLevelWindows()
            if isinstance(window, wx.TextEntryDialog)
        ]
        try:
            assert len(dialogs) == 1, "Expected exactly one text-entry dialog"
            dialog = dialogs[0]
            assert dialog.GetValue() == expected_text
            controls = [
                child
                for child in dialog.GetChildren()
                if isinstance(child, wx.TextCtrl)
            ]
            assert len(controls) == 1
            assert controls[0].HasFlag(wx.TE_PASSWORD) == secret
            dialog.SetValue(entered)
        except Exception as error:
            errors.append(error)
        finally:
            for dialog in dialogs:
                dialog.EndModal(result)

    timer = wx.CallLater(100, respond)
    try:
        answer = prompter.ask("value", field, current)
    finally:
        timer.Stop()
    if errors:
        raise errors[0]
    wx.Yield()
    assert not any(
        isinstance(window, wx.TextEntryDialog) for window in wx.GetTopLevelWindows()
    )
    return answer


def run(ownership):
    """Check repeated collection, cancellation, secrets, and ownership."""
    external_app = wx.App(False) if ownership == "borrowed" else None
    prompter = GuiPrompter(title="Upref integration test")
    app = wx.GetApp()
    assert app is not None
    if external_app is not None:
        assert app is external_app
    try:
        for current in ("first", "second"):
            assert (
                ask_with_response(
                    prompter,
                    Field("Name"),
                    current,
                    entered="updated",
                    result=wx.ID_OK,
                    expected_text=current,
                )
                == "updated"
            )
        assert (
            ask_with_response(
                prompter,
                Field("Flags", formatter=json.dumps),
                [True, None],
                entered="[false]",
                result=wx.ID_OK,
                expected_text="[true, null]",
            )
            == "[false]"
        )
        assert (
            ask_with_response(
                prompter,
                Field("Token", secret=True),
                "existing-secret",
                entered="new-secret",
                result=wx.ID_OK,
                expected_text="",
                secret=True,
            )
            == "new-secret"
        )
        assert (
            ask_with_response(
                prompter,
                Field("Name"),
                "keep",
                entered="discard",
                result=wx.ID_CANCEL,
                expected_text="keep",
            )
            is None
        )

        original_dialog = wx.TextEntryDialog
        failed_dialogs = []

        class FailingDialog(original_dialog):
            """Keep a real native dialog while injecting a display failure."""

            def ShowModal(self):
                """Raise after construction to exercise native resource cleanup."""
                failed_dialogs.append(self)
                raise RuntimeError("injected display failure")

        with patch.object(wx, "TextEntryDialog", FailingDialog):
            try:
                prompter.ask("value", Field("Value"), None)
            except RuntimeError as error:
                assert str(error) == "injected display failure"
            else:
                raise AssertionError("Expected the display failure")
        wx.Yield()
        assert len(failed_dialogs) == 1 and not failed_dialogs[0]

        # collect must propagate cancellation and leave caller-owned UI alive.
        def cancel():
            """Dismiss the dialog through wx's actual modal event loop."""
            for window in wx.GetTopLevelWindows():
                if isinstance(window, wx.TextEntryDialog):
                    window.EndModal(wx.ID_CANCEL)

        timer = wx.CallLater(100, cancel)
        initial = {"name": "keep"}
        try:
            collect({"name": Field("Name")}, initial, interface=prompter, mode="all")
        except PromptCancelled:
            pass
        else:
            raise AssertionError("Expected cancellation")
        finally:
            timer.Stop()
        assert initial == {"name": "keep"}
        assert not prompter._closed
    finally:
        prompter.close()
        prompter.close()
        if external_app is not None:
            assert wx.GetApp() is external_app
            external_app.Destroy()
        else:
            assert wx.GetApp() is None


if __name__ == "__main__":
    run(sys.argv[1])
