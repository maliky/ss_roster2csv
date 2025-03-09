# tests/test_cli.py

import pytest
import subprocess
import sys
import os


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "ss_roster2csv", "--help"], capture_output=True
    )
    assert result.returncode == 0
    out = result.stdout.decode().lower()
    assert "usage" in out


# You might add an integration test with a small PDF (if feasible)
# or a small text file for input.
