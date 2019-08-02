# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

# This file is part of vimiv.
# Copyright 2017-2019 Christian Karl (karlch) <karlch at protonmail dot com>
# License: GNU GPL v3, see the "LICENSE" and "AUTHORS" files for details.

r"""Handler to take care of the current working directory.

The handler stores the current working directory and provides the :func:`chdir` method
to change it::

    from vimiv.api import working_directory

    working_directory.handler.chdir("./my/new/directory")

In addition the directory and current image is monitored using QFileSystemWatcher. Any
changes are exposed via three signals:

* ``loaded`` when the working directory has changed and the content was loaded
* ``changed`` when the content of the current directory has chagned
* ``images_changed`` when the images in the current directory where changed

The first two signals are emitted with the list of images and list of directories in the
working directory as arguments, ``images_changed`` only includes the list of images.
Thus, if your custom class needs to know the current images and/or directories, it can
connect to these signals::

    from PyQt5.QtCore import QObject

    from vimiv import api


    class MyCustomClass(QObject):

        @api.objreg.register
        def __init__(self):
            super().__init__()
            api.working_directory.handler.loaded.connect(self._on_dir_loaded)
            api.working_directory.handler.changed.connect(self._on_dir_changed)
            api.working_directory.handler.images_changed.connect(self._on_im_changed)

        def _on_dir_loaded(self, images, directories):
            print("Loaded new images:", *images, sep="\n", end="\n\n")
            print("Loaded new directories:", *directories, sep="\n", end="\n\n")

        def _on_dir_changed(self, images, directories):
            print("Updated images:", *images, sep="\n", end="\n\n")
            print("Updated directories:", *directories, sep="\n", end="\n\n")

        def _on_im_changed(self, images):
            print("Updated images:", *images, sep="\n", end="\n\n")

Module Attributes:
    handler: The initialized :class:`WorkingDirectoryHandler` object to interact with.
"""

import logging
import time
import os
from typing import cast, List, Tuple, Callable

from PyQt5.QtCore import pyqtSignal, QFileSystemWatcher

from vimiv.utils import files, slot
from . import settings, signals, status


class WorkingDirectoryHandler(QFileSystemWatcher):
    """Handler to store and change the current working directory.

    Signals:
        loaded: Emitted when the content for a new working directory was
                loaded.
            arg1: List of images in the working directory.
            arg2: List of directories in the working directory.
        changed: Emitted when the content of the working directory has changed.
            arg1: List of images in the working directory.
            arg2: List of directories in the working directory.
        images_changed: Emitted when the images in the working directory have
                changed.
            arg1: List of images in the working directory.

    Class Attributes:
        WAIT_TIME: Time to wait before emitting *_changed signals.

    Attributes:
        _dir: The current working directory.
        _images: Images in the current working directory.
        _directories: Directories in the current working directory.
    """

    loaded = pyqtSignal(list, list)
    changed = pyqtSignal(list, list)
    images_changed = pyqtSignal(list)

    WAIT_TIME = 0.3

    def __init__(self) -> None:
        super().__init__()
        self._dir = ""
        self._images: List[str] = []
        self._directories: List[str] = []
        self._processing = False

        settings.monitor_fs.changed.connect(self._on_monitor_fs_changed)
        # TODO Fix upstream and open PR
        self.directoryChanged.connect(self._reload_directory)  # type: ignore
        self.fileChanged.connect(self._on_file_changed)  # type: ignore
        signals.new_image_opened.connect(self._on_new_image)

    def chdir(self, directory: str, reload_current: bool = False) -> None:
        """Change the current working directory to directory."""
        directory = os.path.abspath(directory)
        if directory != self._dir or reload_current:
            if self.directories():  # Unmonitor old directories
                self.removePaths(self.directories())
            try:
                os.chdir(directory)
                self._load_directory(directory)
                self._monitor(directory)
            except PermissionError as e:
                logging.error("%s: Cannot access '%s'", str(e), directory)

    def _monitor(self, directory: str) -> None:
        """Monitor the directory by adding it to QFileSystemWatcher."""
        if not settings.monitor_fs.value:
            return
        if not self.addPath(directory):
            logging.error("Cannot monitor %s", directory)
        else:
            logging.debug("Monitoring %s", directory)

    def _on_monitor_fs_changed(self, value: bool) -> None:
        """Start/stop monitoring when the setting changed."""
        if value:
            self._monitor(self._dir)
        else:
            logging.debug("Turning monitoring off")
            self._stop_monitoring()

    def _load_directory(self, directory: str) -> None:
        """Load supported files for new directory."""
        self._dir = directory
        self._images, self._directories = self._get_content(directory)
        self.loaded.emit(self._images, self._directories)

    @slot
    def _reload_directory(self, _path: str) -> None:
        """Load new supported files when directory content has changed."""
        self._process(lambda: self._emit_changes(*self._get_content(self._dir)))

    @slot
    def _on_new_image(self, path: str) -> None:
        """Monitor the current image for changes."""
        if self.files():  # Clear old image
            self.removePaths(self.files())
        self.addPath(path)

    @slot
    def _on_file_changed(self, path: str) -> None:
        """Emit new_image_opened signal to reload the file on changes."""
        if os.path.exists(path):  # Otherwise the path was deleted
            self._process(signals.image_changed.emit)

    def _process(self, func: Callable[[], None]) -> None:
        """Process function after waiting unless another process is running.

        This is required as images may be written in parts and loading every
        single step is neither possible nor wanted and as tools like mogrify
        from ImageMagick create temporary files which should not be loaded.

        Args:
            func: The function to call when processing.
        """
        if self._processing:
            return
        self._processing = True
        time.sleep(self.WAIT_TIME)
        func()
        self._processing = False
        status.update()

    def _emit_changes(self, images: List[str], directories: List[str]) -> None:
        """Emit changed signals if the content in the directory has changed.

        Args:
            images: Updated list of images in the working directory.
            directories: Updated list of directories in the working directory.
        """
        # Image filelist has changed, relevant for thumbnail and image mode
        if images != self._images:
            self.images_changed.emit(images)
        # Total filelist has changed, relevant for the library
        if images != self._images or directories != self._directories:
            self._images = images
            self._directories = directories
            self.changed.emit(images, directories)

    def _get_content(self, directory: str) -> Tuple[List[str], List[str]]:
        """Get supported content of directory.

        Returns:
            images: List of images inside the directory.
            directories: List of directories inside the directory.
        """
        show_hidden = settings.library.show_hidden.value
        paths = files.listdir(directory, show_hidden=show_hidden)
        return files.supported(paths)


handler = cast(WorkingDirectoryHandler, None)


def init() -> None:
    """Initialize handler.

    This is required as working_directory is imported by the application but
    the QFileSystemWatcher only works appropriately once an application has
    been created.
    """
    global handler
    handler = WorkingDirectoryHandler() if handler is None else handler
