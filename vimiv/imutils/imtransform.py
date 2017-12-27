# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Perform simple transformations like rotate and flip."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTransform

from vimiv.commands import commands
from vimiv.config import keybindings
from vimiv.imutils import imcommunicate, imloader
from vimiv.utils import objreg


class Transform():

    @objreg.register("transform")
    def __init__(self, image_file_handler):
        self._parent = image_file_handler
        self._transform = QTransform()
        self._rotation_angle = 0
        self._flip_horizontal = self._flip_vertical = False

    @keybindings.add("<", "rotate --counter-clockwise")
    @keybindings.add(">", "rotate")
    @commands.argument("counter-clockwise", optional=True, action="store_true")
    @commands.register(mode="image", count=1, instance="transform")
    def rotate(self, counter_clockwise, count):
        """Rotate the image.

        Args:
            counter_clockwise: Rotate counter clockwise.
        """
        angle = 90 * count * -1 if counter_clockwise else 90 * count
        self._rotation_angle += angle
        self._transform.rotate(angle)
        pixmap = self.transform_pixmap(imloader.current())
        imcommunicate.signals.pixmap_loaded.emit(pixmap)

    @keybindings.add("_", "flip --vertical")
    @keybindings.add("|", "flip")
    @commands.argument("vertical", optional=True, action="store_true")
    @commands.register(mode="image", instance="transform")
    def flip(self, vertical):
        """Flip the image.

        Args:
            vertical: Flip image vertically instead of horizontally.
        """
        # Vertical flip but image rotated by 90 degrees
        if (vertical and self._rotation_angle % 180):
            self._transform.scale(-1, 1)
        # Standard vertical flip
        elif vertical:
            self._transform.scale(1, -1)
        # Horizontal flip but image rotated by 90 degrees
        elif self._rotation_angle % 180:
            self._transform.scale(1, -1)
        # Standard horizontal flip
        else:
            self._transform.scale(-1, 1)
        pixmap = self.transform_pixmap(imloader.current())
        # Store changes
        if vertical:
            self._flip_vertical = not self._flip_vertical
        else:
            self._flip_horizontal = not self._flip_horizontal
        imcommunicate.signals.pixmap_loaded.emit(pixmap)

    def transform_pixmap(self, pm):
        return pm.transformed(self._transform, mode=Qt.SmoothTransformation)

    def changed(self):
        if self._rotation_angle or self._flip_horizontal or self._flip_vertical:
            return True
        return False

    def reset(self):
        self._transform.reset()
        self._rotation_angle = 0
        self._flip_horizontal = self._flip_vertical = False