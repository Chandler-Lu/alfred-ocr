'''Mathpix formula recognition.

https://docs.mathpix.com/#request-parameters
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json

from core import http_client
from core.base_provider import BaseProvider, OcrResult
from core.exceptions import ApiError
from core.image_loader import ImageFile


class MathpixFormulaOcr(BaseProvider):
    name = 'mathpix'
    aliases = ('oom',)
    selector = 7
    summary = 'Mathpix formula recognition (LaTeX)'
    required_credentials = ('mathpix_app_id', 'mathpix_app_key')

    def recognize(self, payload: ImageFile) -> OcrResult:
        response = http_client.post_json(
            self.settings.str('mathpix_api'),
            headers={
                'app_id': self.settings.credential('mathpix_app_id'),
                'app_key': self.settings.credential('mathpix_app_key'),
                'Content-type': 'application/json',
            },
            data=json.dumps({'src': payload.data_uri(max_bytes=self.max_bytes)}),
        )
        if response.get('error'):
            raise ApiError(str(response['error']))
        # LaTeX must survive untouched.
        return OcrResult.raw(
            str(response.get('latex_styled')
                or response.get('text') or '')).or_raise()
