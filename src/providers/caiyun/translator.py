'''Caiyun translation.

Not an OCR engine, but it shares the credential handling, the HTTP client and
the router, so it is modelled as a text-in provider.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json
import re
import time
from typing import Optional

from core import http_client
from core.base_provider import INPUT_TEXT, BaseProvider, OcrResult
from core.exceptions import ApiError
from utils.punctuation import latin_ratio

# Kana and Hangul share the Han block with Chinese but are never zh2en input.
_NOT_CHINESE_RE = re.compile(r'[\u3040-\u30ff\uac00-\ud7af]')


def detect_direction(text: str) -> str:
    '''Chinese in, English out; anything else in, Chinese out.'''
    if _NOT_CHINESE_RE.search(text):
        return 'auto2zh'
    return 'zh2en' if latin_ratio(text) < 0.5 else 'auto2zh'


class CaiyunTranslator(BaseProvider):
    name = 'translate'
    aliases = ('tc', 'caiyun')
    summary = 'Caiyun translation (Chinese <-> other languages)'
    input_kind = INPUT_TEXT
    # Alfred shows the translation in the result list and copies it on Enter.
    output_format = 'alfred'
    required_credentials = ('caiyun_token',)

    def recognize(self, payload: str) -> OcrResult:
        return OcrResult.raw(self.translate(str(payload or '')))

    def translate(self, source: str, direction: Optional[str] = None) -> str:
        source = source.strip()
        if not source:
            raise ApiError('Nothing to translate')
        response = http_client.post_json(
            self.settings.str('caiyun_translate_api'),
            headers={
                'Content-Type': 'application/json',
                'X-Authorization': 'token ' + self.settings.credential('caiyun_token'),
            },
            data=json.dumps({
                'source': source,
                'request_id': str(time.time()),
                'trans_type': direction or detect_direction(source),
                'detect': 'True',
            }),
        )
        target = response.get('target')
        if isinstance(target, list):
            target = '\n'.join(str(item) for item in target)
        if not target:
            raise ApiError(str(response.get('message') or 'Translation failed!'))
        return str(target)
