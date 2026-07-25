'''Google Cloud Vision text detection.'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json

from core import http_client
from core.base_provider import BaseProvider, OcrResult
from core.exceptions import ApiError
from core.image_loader import ImageFile


class GoogleGeneralOcr(BaseProvider):
    name = 'google'
    aliases = ('oog',)
    selector = 5
    summary = 'Google Cloud Vision text detection'
    required_credentials = ('google_access_token',)

    def recognize(self, payload: ImageFile) -> OcrResult:
        headers = {'Content-Type': 'application/json'}
        referer = self.settings.credential('google_post_referer')
        if referer:
            headers['Referer'] = referer

        response = http_client.post_json(
            self.settings.str('google_ocr_api'),
            params={'key': self.settings.credential('google_access_token')},
            headers=headers,
            data=json.dumps({
                'requests': [{
                    'image': {'content': payload.base64(self.max_bytes)},
                    'features': [{'type': 'TEXT_DETECTION'}],
                }],
            }),
        )

        responses = response.get('responses') or [{}]
        first = responses[0] if isinstance(responses[0], dict) else {}
        if 'error' in first:
            raise ApiError('Error: ' + str(first['error'].get(
                'message', 'Google OCR failed')))
        annotations = first.get('textAnnotations') or []
        if not annotations:
            return OcrResult.from_text('').or_raise()
        # Vision already returns the page layout, so keep its line breaks and
        # only run the punctuation and spacing clean-up.
        return OcrResult.from_text(
            str(annotations[0].get('description', '')).rstrip('\n'))
