# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2022 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

import pytest
import pytest_bdd as bdd

import vimiv.gui.straightenwidget


bdd.scenarios("straighten.feature")


def find_straighten_widgets(image):
    return image.findChildren(vimiv.gui.straightenwidget.StraightenWidget)


@pytest.fixture()
def straighten(image):
    """Fixture to retrieve the current instance of the straighten widget."""
    widgets = find_straighten_widgets(image)
    assert len(widgets) == 1, "Wrong number of straighten wigets found"
    return widgets[0]


@bdd.when(bdd.parsers.parse("I straighten by {angle:g} degrees"))
@bdd.when(bdd.parsers.parse("I straighten by {angle:g} degree"))
def straighten_by(qtbot, straighten, angle):
    def check():
        assert (straighten.transform.angle) % 90 == pytest.approx(expected_angle % 90)

    expected_angle = straighten.angle + angle

    straighten.rotate(angle=angle)
    qtbot.waitUntil(check)


@bdd.when(bdd.parsers.parse("I press '{keys}' in the straighten widget"))
def press_key_straighten(keypress, straighten, keys):
    keypress(straighten, keys)


@bdd.then(bdd.parsers.parse("there should be {number:d} straighten widgets"))
@bdd.then(bdd.parsers.parse("there should be {number:d} straighten widget"))
def check_number_of_straighten_widgets(qtbot, image, number):
    def check():
        assert len(find_straighten_widgets(image)) == number

    qtbot.waitUntil(check)


@bdd.then(bdd.parsers.parse("the straighten angle should be {angle:.f}"))
def check_straighten_angle(qtbot, straighten, angle):
    def check():
        assert straighten.angle == pytest.approx(angle)

    qtbot.waitUntil(check)
