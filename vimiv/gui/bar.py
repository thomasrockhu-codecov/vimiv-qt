# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Bar widget at the bottom including statusbar and commandline."""

from PyQt5.QtWidgets import QWidget, QStackedLayout, QSizePolicy

from vimiv.commands import commands
from vimiv.config import keybindings, settings
from vimiv.gui import commandline, statusbar
from vimiv.modes import modehandler
from vimiv.utils import objreg


class Bar(QWidget):
    """Bar at the bottom including statusbar and commandline.

    Attributes:
        statusbar: vimiv.gui.statusbar.StatusBar object.
        commandline: vimiv.gui.commandline.CommandLine object.

        _stack: QStackedLayout containing statusbar and commandline.
    """

    @objreg.register("bar")
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        self._stack = QStackedLayout(self)
        self.statusbar = statusbar.StatusBar()
        self._stack.addWidget(self.statusbar)
        self.commandline = commandline.CommandLine()
        self._stack.addWidget(self.commandline)
        self._stack.setCurrentWidget(self.statusbar)
        self._maybe_hide()

        self.commandline.editingFinished.connect(self._on_editing_finished)
        settings.signals.changed.connect(self._on_settings_changed)

    @keybindings.add("<colon>", "command")
    @commands.argument("text", optional=True, default="")
    @commands.register(instance="bar", hide=True)
    def command(self, text=""):
        """Enter command mode."""
        self.show()
        self._stack.setCurrentWidget(self.commandline)
        if text:
            text += " "
        self.commandline.setText(":" + text)
        modehandler.enter("command")

    @keybindings.add("<escape>", "leave-commandline", mode="command")
    @commands.register(instance="bar", mode="command")
    def leave_commandline(self):
        """Leave command mode."""
        self.commandline.editingFinished.emit()

    def _on_editing_finished(self):
        """Leave command mode on the editingFinished signal."""
        self.commandline.setText("")
        self._stack.setCurrentWidget(self.statusbar)
        modehandler.leave("command")
        self._maybe_hide()

    def _on_settings_changed(self, setting, new_value):
        """React to changed settings."""
        if setting == "statusbar.show":
            self.statusbar.setVisible(new_value)
            self._maybe_hide()
        elif setting == "statusbar.timeout":
            self.statusbar.timer.setInterval(new_value)

    def _maybe_hide(self):
        """Hide bar if statusbar is not visible and not in command mode."""
        always_show = settings.get_value("statusbar.show")
        if not always_show and not self.commandline.hasFocus():
            self.hide()
        else:
            self.show()
