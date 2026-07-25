'''Baidu general OCR, plus the multi-file variant that reuses it.'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from core import image_loader
from core.base_provider import (INPUT_DIRECTORY, BaseProvider, OcrResult)
from core.exceptions import ImageError, OcrError
from core.image_loader import ImageFile
from core.layout import TextLine
from providers.baidu import client


def lines_from_response(words_result: Iterable[Mapping[str, Any]]) -> List[TextLine]:
    lines = []
    for item in words_result:
        location = item.get('location') or {}
        lines.append(TextLine.from_box(
            item.get('words', ''),
            left=location.get('left'), top=location.get('top'),
            width=location.get('width'), height=location.get('height')))
    return lines


class BaiduGeneralOcr(BaseProvider):
    name = 'baidu'
    aliases = ('oob', 'baidu-general')
    selector = 1
    summary = 'Baidu general OCR (text, with paragraph reconstruction)'
    required_credentials = ('baidu_api_key', 'baidu_secret_key')
    max_bytes_setting = 'baidu_max_image_bytes'

    def recognize(self, payload: ImageFile) -> OcrResult:
        response = client.request(
            'baidu_ocr_api', payload, self.max_bytes,
            {'language_type': self.settings.str('baidu_language_type')})
        return OcrResult.from_lines(
            lines_from_response(response.get('words_result') or [])).or_raise()


class BaiduMultiFileOcr(BaseProvider):
    '''Every image in a directory, recognized with the general endpoint.'''

    name = 'baidu-multi-file'
    aliases = ('multi', 'oof')
    selector = 99
    summary = 'Baidu OCR over every image in the drop folder'
    input_kind = INPUT_DIRECTORY
    required_credentials = ('baidu_api_key', 'baidu_secret_key')

    def recognize(self, payload: Any) -> OcrResult:
        directory = payload or self.settings.str('multi_file_path')
        general = BaiduGeneralOcr(self.settings)
        images = image_loader.list_images(directory, general.max_bytes)
        if not images:
            raise ImageError('Error: no files to recognize!')

        blocks: List[str] = []
        for image in images:
            try:
                blocks.append(general.run(image).render())
            except OcrError as error:
                # One unreadable page must not lose the other twenty.
                blocks.append(error.message)
            finally:
                image.discard()
        return OcrResult.raw('\n\n'.join(block for block in blocks if block))
