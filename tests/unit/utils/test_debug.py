# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Tests for vimiv.utils.debug"""

import time
import re

import pytest

from vimiv.utils import debug


def test_profiler(capsys):
    with debug.profile(5):
        pass
    assert "function calls" in capsys.readouterr().out


def test_timed(mocker, capsys):
    mocker.patch("vimiv.utils.log.info")
    expected = 42
    sleep_time_ms = 1

    @debug.timed
    def func():
        time.sleep(sleep_time_ms / 1000)
        return expected

    result = func()

    assert result == expected  # Ensure the result is preserved
    captured = capsys.readouterr()
    assert func.__name__ in captured.out  # Ensure a message was printed
    # Ensure the message contains the elapsed time
    time_match = re.search(r"\d+.\d+", captured.out)
    assert time_match is not None, "No time logged"
    message_time = float(time_match.group())
    assert message_time == pytest.approx(sleep_time_ms, sleep_time_ms)