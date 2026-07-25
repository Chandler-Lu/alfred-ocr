'''Tencent Cloud OCR, signed with TC3-HMAC-SHA256.

The detected boxes are returned as TextLine objects, so Tencent results go
through the same paragraph reconstruction as Baidu's instead of getting one
hard newline per recognized line.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, List, Mapping

from core import http_client
from core.base_provider import BaseProvider, OcrResult
from core.exceptions import ApiError
from core.image_loader import ImageFile
from core.layout import TextLine

ALGORITHM = 'TC3-HMAC-SHA256'
SIGNED_HEADERS = 'content-type;host'
CONTENT_TYPE = 'application/json; charset=utf-8'


def sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode('utf-8'), hashlib.sha256).digest()


def line_from_detection(detection: Mapping[str, Any]) -> TextLine:
    text = str(detection.get('DetectedText', ''))
    box = detection.get('ItemPolygon') or {}
    if box:
        return TextLine.from_box(text, left=box.get('X'), top=box.get('Y'),
                                 width=box.get('Width'), height=box.get('Height'))
    return TextLine.from_polygon(text, detection.get('Polygon') or [])


class TencentGeneralOcr(BaseProvider):
    name = 'tencent'
    aliases = ('oot',)
    selector = 4
    summary = 'Tencent Cloud general OCR'
    required_credentials = ('tencent_secret_id', 'tencent_secret_key')
    max_bytes_setting = 'tencent_max_image_bytes'

    def recognize(self, payload: ImageFile) -> OcrResult:
        body = json.dumps({'ImageBase64': payload.base64(self.max_bytes)})
        request_payload = body.encode('utf-8')
        timestamp = int(time.time())

        response = http_client.post_json(
            self.settings.str('tencent_ocr_api'),
            headers={
                'Content-Type': CONTENT_TYPE,
                'X-TC-Action': self.settings.str('tencent_action'),
                'X-TC-Region': self.settings.str('tencent_region'),
                'X-TC-Timestamp': str(timestamp),
                'X-TC-Version': self.settings.str('tencent_version'),
                'Authorization': self.authorization(request_payload, timestamp),
            },
            data=request_payload,
        )

        result = response.get('Response') or {}
        if 'Error' in result:
            raise ApiError(str(result['Error'].get('Message',
                                                   'Tencent OCR failed')))
        detections = result.get('TextDetections') or []
        lines: List[TextLine] = [line_from_detection(item) for item in detections]
        return OcrResult.from_lines(lines).or_raise()

    def authorization(self, payload: bytes, timestamp: int) -> str:
        secret_id = self.settings.credential('tencent_secret_id')
        secret_key = self.settings.credential('tencent_secret_key')
        service = 'ocr'
        date = datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d')

        canonical_request = '\n'.join([
            'POST',
            '/',
            '',
            'content-type:%s\nhost:%s\n' % (
                CONTENT_TYPE, self.settings.str('tencent_ocr_host')),
            SIGNED_HEADERS,
            hashlib.sha256(payload).hexdigest().lower(),
        ])
        credential_scope = '/'.join([date, service, 'tc3_request'])
        string_to_sign = '\n'.join([
            ALGORITHM,
            str(timestamp),
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest(),
        ])

        secret_date = sign(('TC3' + secret_key).encode('utf-8'), date)
        secret_service = sign(secret_date, service)
        secret_signing = sign(secret_service, 'tc3_request')
        signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'),
                             hashlib.sha256).hexdigest()

        return (ALGORITHM + ' Credential=' + secret_id + '/' + credential_scope
                + ', SignedHeaders=' + SIGNED_HEADERS
                + ', Signature=' + signature)
