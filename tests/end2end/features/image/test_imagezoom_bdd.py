# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2022 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

import pytest
import pytest_bdd as bdd


bdd.scenarios("imagezoom.feature")


@bdd.then(bdd.parsers.parse("the zoom level should be {level:f}"))
def check_zoom_level(image, level):
    assert level == pytest.approx(image.zoom_level, 0.01)


@bdd.then(bdd.parsers.parse("the zoom level should not be {level:f}"))
def check_zoom_level_not(image, level):
    assert level != pytest.approx(image.zoom_level, 0.01)
