# vim: ft=python fileencoding=utf-8 sw=4 et sts=4

from vimiv.utils import lazy


def test_dummy():
    pyexiv2 = lazy.import_module("pyexiv2", optional=True)
    metadata_cls = pyexiv2.ImageMetadata
    assert metadata_cls is not None
