# -*- coding: UTF-8 -*-
import base64

import pytest

from core import image_loader
from core.exceptions import ImageError
from core.image_loader import ImageFile


def test_load_a_local_file(image_file):
    loaded = image_loader.load(image_file.path)
    assert loaded.path == image_file.path
    assert not loaded.temporary


def test_load_rejects_a_missing_file(tmp_path):
    with pytest.raises(ImageError):
        image_loader.load(str(tmp_path / 'nope.png'))


def test_load_rejects_an_empty_source():
    with pytest.raises(ImageError):
        image_loader.load('')


def test_read_and_base64(image_file):
    data = image_file.read()
    assert data.startswith(b'\x89PNG')
    assert base64.b64decode(image_file.base64()) == data
    assert image_file.data_uri().startswith('data:image/jpg;base64,')


def test_bytes_are_read_only_once(image_file, monkeypatch):
    image_file.read()
    monkeypatch.setattr('builtins.open', _explode)
    assert image_file.read().startswith(b'\x89PNG')


def test_size_limit(image_file):
    with pytest.raises(ImageError) as error:
        image_file.read(max_bytes=8)
    assert error.value.message == 'Too large!'


def test_empty_file_is_refused(tmp_path):
    path = tmp_path / 'empty.png'
    path.write_bytes(b'')
    with pytest.raises(ImageError):
        ImageFile(path=str(path)).read()


def test_unreadable_file(tmp_path):
    missing = ImageFile(path=str(tmp_path / 'gone.png'))
    with pytest.raises(ImageError):
        missing.read()


def test_discard_removes_the_file(image_file):
    assert image_file.discard()
    assert not image_file.discard()


def test_list_images_is_sorted_and_filtered(tmp_path):
    for name in ('b.png', 'a.jpg', 'notes.txt', 'c.PNG'):
        (tmp_path / name).write_bytes(b'x' * 16)
    (tmp_path / 'huge.png').write_bytes(b'x' * 4096)
    (tmp_path / 'sub.png').mkdir()

    images = image_loader.list_images(str(tmp_path), max_bytes=1024)
    assert [image.name for image in images] == ['a.jpg', 'b.png', 'c.PNG']


def test_list_images_on_a_missing_directory(tmp_path):
    with pytest.raises(ImageError):
        image_loader.list_images(str(tmp_path / 'nope'))


def test_load_from_url(monkeypatch, tmp_path):
    from core import http_client

    def fake_download(url, destination, timeout=None):
        with open(destination, 'wb') as handle:
            handle.write(b'\x89PNG downloaded')
        return destination

    monkeypatch.setattr(http_client, 'download', fake_download)
    loaded = image_loader.load('https://example.com/shot.png')
    try:
        assert loaded.temporary
        assert loaded.read() == b'\x89PNG downloaded'
    finally:
        loaded.discard()


def test_a_failed_download_leaves_no_temporary_file(monkeypatch):
    from core import http_client
    from core.exceptions import ApiError

    seen = {}

    def fake_download(url, destination, timeout=None):
        seen['path'] = destination
        raise ApiError('Request failed!')

    monkeypatch.setattr(http_client, 'download', fake_download)
    with pytest.raises(ApiError):
        image_loader.load('https://example.com/shot.png')
    import os
    assert not os.path.exists(seen['path'])


def test_clipboard_source(monkeypatch):
    from utils import clipboard

    def fake_paste(destination):
        with open(destination, 'wb') as handle:
            handle.write(b'\x89PNG clipboard')
        return destination

    monkeypatch.setattr(clipboard, 'paste_image', fake_paste)
    loaded = image_loader.load('-')
    try:
        assert loaded.read() == b'\x89PNG clipboard'
    finally:
        loaded.discard()


def test_empty_clipboard(monkeypatch):
    from utils import clipboard

    monkeypatch.setattr(clipboard, 'paste_image', lambda destination: None)
    with pytest.raises(ImageError):
        image_loader.load('clipboard')


def _explode(*args, **kwargs):
    raise AssertionError('the file was read twice')
