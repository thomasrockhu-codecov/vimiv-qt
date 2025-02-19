# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2022 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Tests for vimiv.commands.runners."""

import pytest

from vimiv.commands import runners


@pytest.mark.parametrize("text", [" ", "\n", " \n", "\t\t", "\n \t"])
def test_text_non_whitespace_with_whitespace(text):
    """Ensure the decorated function is not called with plain whitespace."""

    @runners.text_non_whitespace
    def function(text):
        raise AssertionError("The function should not be called")

    function(text)


@pytest.mark.parametrize("text", [" txt", "\ntxt", " \ntxt", "\ttxt\t", "\n txt\t"])
def test_text_non_whitespace_with_non_whitespace(text):
    """Ensure the decorated function is called with stripped text."""

    @runners.text_non_whitespace
    def function(stripped_text):
        """Function to ensure any surrounding whitespace is removed."""
        assert stripped_text == text.strip()

    function(text)
