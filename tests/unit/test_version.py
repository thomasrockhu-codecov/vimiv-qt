# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2022 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Tests for vimiv.version."""

import pytest

from vimiv import version
from vimiv.imutils import exif


@pytest.fixture
def no_svg_support(monkeypatch):
    monkeypatch.setattr(version, "QtSvg", None)


def test_svg_support_info():
    assert "svg support: true" in version.info().lower()


def test_no_svg_support_info(no_svg_support):
    assert "svg support: false" in version.info().lower()


@pytest.mark.pyexiv2
def test_pyexiv2_info():
    assert exif.pyexiv2.__version__ in version.info()


@pytest.mark.piexif
def test_piexif_info():
    assert exif.piexif.VERSION in version.info()


def test_no_exif_support_info(noexif):
    assert "piexif: none" in version.info().lower()
    assert "pyexiv2: none" in version.info().lower()
