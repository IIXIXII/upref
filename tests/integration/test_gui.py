"""Opt-in native wxPython scenarios, isolated to bound GUI hangs and app state."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(
        os.environ.get("UPREF_RUN_GUI_TESTS") != "1",
        reason="Set UPREF_RUN_GUI_TESTS=1 in a desktop session to test native wxPython",
    ),
]


@pytest.mark.parametrize("ownership", ["owned", "borrowed"])
def test_native_dialogs_and_application_lifecycle(ownership):
    scenario = Path(__file__).with_name("_gui_scenario.py")
    result = subprocess.run(
        [sys.executable, str(scenario), ownership],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
