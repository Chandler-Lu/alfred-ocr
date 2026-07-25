'''Baidu QR code recognition, one block per code.'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Any, Mapping, Sequence

from core.base_provider import BaseProvider, OcrResult
from core.exceptions import EmptyResultError
from core.image_loader import ImageFile
from providers.baidu import client


def format_codes(codes: Sequence[Mapping[str, Any]]) -> str:
    groups = []
    for index, code in enumerate(codes):
        body = '\n'.join(str(text) for text in code.get('text') or []
                         if str(text).strip())
        if not body:
            continue
        groups.append(body if len(codes) == 1
                      else 'Group ' + str(index + 1) + '\n' + body)
    if not groups:
        raise EmptyResultError('Empty QR Code!')
    return '\n\n'.join(groups)


class BaiduQrReader(BaseProvider):
    name = 'baidu-qrcode'
    aliases = ('qrcode-baidu', 'ooqb')
    selector = 2
    summary = 'Baidu QR code recognition (multiple codes supported)'
    required_credentials = ('baidu_api_key', 'baidu_secret_key')
    max_bytes_setting = 'baidu_max_image_bytes'

    def recognize(self, payload: ImageFile) -> OcrResult:
        response = client.request('baidu_qrcode_api', payload, self.max_bytes)
        # A QR payload is a URL or an id: formatting it would corrupt it.
        return OcrResult.raw(format_codes(response.get('codes_result') or []))
