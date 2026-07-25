'''Image input: local file, remote URL or the macOS clipboard.

A provider receives an ImageFile and asks it for bytes, base64 or a path -
whichever its SDK needs - without caring where the picture came from. Size
limits are enforced here, before an oversized upload is attempted.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import tempfile
from base64 import b64encode
from dataclasses import dataclass, field
from typing import List, Optional

from core.config import settings
from core.exceptions import ImageError
from utils import clipboard

CLIPBOARD_TOKENS = ('-', 'clipboard', 'pasteboard')
URL_PREFIXES = ('http://', 'https://')


@dataclass
class ImageFile:
    '''One image on disk, plus how to get rid of it afterwards.'''

    path: str
    temporary: bool = False
    _data: Optional[bytes] = field(default=None, repr=False)

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def size(self) -> int:
        try:
            return os.path.getsize(self.path)
        except OSError as error:
            raise ImageError('Error: image not found!') from error

    def check_size(self, max_bytes: Optional[int]) -> None:
        size = self.size
        if size == 0:
            raise ImageError('Error: empty image!')
        if max_bytes is not None and size > max_bytes:
            raise ImageError('Too large!')

    def read(self, max_bytes: Optional[int] = None) -> bytes:
        self.check_size(max_bytes)
        if self._data is None:
            try:
                with open(self.path, 'rb') as handle:
                    self._data = handle.read()
            except OSError as error:
                raise ImageError('Error: image unreadable!') from error
        return self._data

    def base64(self, max_bytes: Optional[int] = None) -> str:
        return b64encode(self.read(max_bytes)).decode('utf-8')

    def data_uri(self, mime: str = 'image/jpg',
                 max_bytes: Optional[int] = None) -> str:
        return 'data:' + mime + ';base64,' + self.base64(max_bytes)

    def discard(self) -> bool:
        '''Delete the file. Screenshots are throw-away by contract.'''
        if not os.path.isfile(self.path):
            return False
        try:
            os.remove(self.path)
            return True
        except OSError:
            return False


def load(source: str) -> ImageFile:
    '''Resolve ``source`` - a path, an http(s) URL, or '-' for the clipboard.'''
    if not source:
        raise ImageError('Error: no image given!')
    if source.lower().startswith(URL_PREFIXES):
        return _load_url(source)
    if source.lower() in CLIPBOARD_TOKENS:
        return _load_clipboard()
    if not os.path.isfile(source):
        raise ImageError('Error: image not found!')
    return ImageFile(path=source)


def _temporary_path(suffix: str = '.png') -> str:
    handle, path = tempfile.mkstemp(prefix='alfred-ocr-', suffix=suffix)
    os.close(handle)
    return path


def _load_url(url: str) -> ImageFile:
    from core import http_client  # imported late: keeps offline providers light

    suffix = os.path.splitext(url.split('?')[0])[1] or '.png'
    path = _temporary_path(suffix)
    try:
        http_client.download(url, path)
    except Exception:
        ImageFile(path=path, temporary=True).discard()
        raise
    return ImageFile(path=path, temporary=True)


def _load_clipboard() -> ImageFile:
    path = _temporary_path()
    if clipboard.paste_image(path) is None:
        ImageFile(path=path, temporary=True).discard()
        raise ImageError('Error: no image in the clipboard!')
    return ImageFile(path=path, temporary=True)


def list_images(directory: str, max_bytes: Optional[int] = None) -> List[ImageFile]:
    '''Sorted images in ``directory``, skipping anything oversized.'''
    try:
        names = sorted(os.listdir(directory))
    except OSError as error:
        raise ImageError('Error: no files to recognize!') from error

    extensions = tuple(settings.list('image_extensions'))
    images: List[ImageFile] = []
    for name in names:
        if not name.lower().endswith(extensions):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        if max_bytes is not None and os.path.getsize(path) > max_bytes:
            continue
        images.append(ImageFile(path=path))
    return images
