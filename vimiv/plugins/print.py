# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

"""Plugin enabling print support."""

import abc
from typing import cast, Optional, Union, Any

from PyQt5.QtCore import QObject, Qt, QSize
from PyQt5.QtGui import QPixmap, QMovie, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter

# We need the check as svg support is optional
try:
    from PyQt5.QtSvg import QSvgWidget
except ImportError:
    QSvgWidget = None

from vimiv import api
from vimiv.utils import slot, log


_logger = log.module_logger(__name__)


class PrintHandler(QObject):
    """Printing class which adds the :print command.

    The class connects to the differend loaded signals of imutils to create the correct
    PrintWidget for the currently displayed image type. Once print is called the
    QPrint(Preview)Dialog is started and upon confirmation the widget is printed.

    Attributes:
        _widget: Currently displayed PrintWidget to print.
    """

    @api.objreg.register
    def __init__(self) -> None:
        super().__init__()

        self._widget: Optional[PrintWidget] = None

        api.signals.pixmap_loaded.connect(self._on_pixmap_loaded)
        api.signals.movie_loaded.connect(self._on_movie_loaded)
        api.signals.svg_loaded.connect(self._on_svg_loaded)

    @api.commands.register(mode=api.modes.IMAGE)
    def print(self, preview: bool = False) -> None:
        """Print the current widget.

        **syntax:** ``:print [--preview]``

        optional arguments:
            * ``--preview``: Show preview dialog before printing.
        """
        if self._widget is None:
            raise api.commands.CommandError("No widget to print")

        _logger.debug("Starting print dialog")

        def handle_print() -> None:
            # We only use handle_print in the function below, None was caught above
            self._widget = cast(PrintWidget, self._widget)
            self._widget.print(dialog.printer(), auto_apply_orientation)

        if preview:
            dialog = QPrintPreviewDialog()
            dialog.paintRequested.connect(handle_print)
            auto_apply_orientation = False
        else:
            dialog = QPrintDialog()
            auto_apply_orientation = True

        dialog.open(handle_print)

    @slot
    def _on_pixmap_loaded(self, pixmap: QPixmap) -> None:
        self._widget = PrintPixmap(pixmap)

    @slot
    def _on_svg_loaded(self, path: str) -> None:
        self._widget = PrintSvg(QSvgWidget(path))

    @slot
    def _on_movie_loaded(self, movie: QMovie) -> None:
        self._widget = PrintMovie(movie)


class PrintWidget(abc.ABC):
    """Base class for printable widgets.

    The base class sets up the printer orientation and the painter. Children must
    implement paint to paint themselves for printing.
    """

    def __init__(self, qwidget: Union[QPixmap, QMovie, QSvgWidget]):
        self._widget = qwidget

    def print(self, printer: QPrinter, auto_apply_orientation: bool = False) -> None:
        """Print the widget."""
        if auto_apply_orientation and self.size().width() > self.size().height():
            printer.setOrientation(QPrinter.Landscape)
        self.paint(printer)

    @abc.abstractmethod
    def paint(self, printer: QPrinter) -> None:
        pass

    def size(self) -> QSize:
        return self._widget.size()


class PrintPixmap(PrintWidget):
    """Print class for pixmap images."""

    def paint(self, printer: QPrinter) -> None:
        """Scale pixmap to match printer page and paint using painter."""
        _logger.debug("Painting pixmap for print")
        painter = QPainter(printer)
        scaled_pixmap = self._widget.scaled(
            printer.pageRect().size(), Qt.KeepAspectRatio
        )
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()


class PrintSvg(PrintWidget):
    """Print class for svg vector graphics."""

    def paint(self, printer: QPrinter) -> None:
        """Scale vector graphic to match printer page and paint using render."""
        _logger.debug("Painting vector graphic for print")
        scale = min(
            self._widget.sizeHint().width() / printer.pageRect().width(),
            self._widget.sizeHint().height() / printer.pageRect().height(),
        )
        self._widget.setFixedSize(self._widget.sizeHint() * scale)
        self._widget.render(printer)

    def size(self) -> QSize:
        return self._widget.sizeHint()


class PrintMovie(PrintWidget):
    """Print class for anmiations."""

    def paint(self, printer: QPrinter) -> None:
        """Paint every frame of the movie on one printer page."""
        _logger.debug("Painting animation for print")
        painter = QPainter(printer)

        for frame in range(self._widget.frameCount()):  # Iterate over all frames
            _logger.debug("Painting frame %d", frame)

            if frame > 0:  # Every frame on its own page
                _logger.debug("Adding new page for printer")
                printer.newPage()

            self._widget.jumpToFrame(frame)
            pixmap = self._widget.currentPixmap().scaled(
                printer.pageRect().size(), Qt.KeepAspectRatio
            )
            painter.drawPixmap(0, 0, pixmap)

        painter.end()

    def size(self) -> QSize:
        return self._widget.currentPixmap().size()


def init(_info: str, *_args: Any, **_kwargs: Any) -> None:
    """Setup print plugin by initializing the PrintHandler class."""
    PrintHandler()