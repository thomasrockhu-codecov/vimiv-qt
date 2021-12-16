# vim: ft=python fileencoding=utf-8 sw=4 et sts=4


def test_dummy():
    import pyexiv2

    metadata_cls = pyexiv2.ImageMetadata
    assert metadata_cls is not None
