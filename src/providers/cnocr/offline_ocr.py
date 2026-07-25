'''CnOCR: local model or the FastAPI service mode.

https://github.com/breezedeus/CnOCR
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Any, List, Mapping, Sequence

from core import http_client
from core.base_provider import BaseProvider, OcrResult
from core.exceptions import DependencyError
from core.image_loader import ImageFile
from core.layout import TextLine


def line_from_result(item: Mapping[str, Any]) -> TextLine:
    '''CnOCR reports a four-corner polygon, or nothing for single-line models.'''
    return TextLine.from_polygon(str(item.get('text', '')), item.get('position'))


class CnOcrOffline(BaseProvider):
    name = 'cnocr'
    aliases = ('ooc', 'offline')
    selector = 0
    summary = 'CnOCR offline recognition (local model or local HTTP service)'

    def recognize(self, payload: ImageFile) -> OcrResult:
        results = (self.recognize_over_http(payload) if
                   self.settings.int('cnocr_serve') else
                   self.recognize_locally(payload))
        lines: List[TextLine] = [line_from_result(item) for item in results]
        return OcrResult.from_lines(lines).or_raise()

    def recognize_over_http(self, payload: ImageFile) -> Sequence[Mapping[str, Any]]:
        response = http_client.post_json(
            self.settings.str('cnocr_api'),
            files={'image': (payload.name, payload.read())},
            timeout=self.settings.float('cnocr_timeout'),
            retries=0,
        )
        return response.get('results') or []

    def recognize_locally(self, payload: ImageFile) -> Sequence[Mapping[str, Any]]:
        try:
            from cnocr import CnOcr
        except ImportError as error:
            raise DependencyError('Error: cnocr is not installed!') from error
        engine = CnOcr(rec_model_name=self.settings.str('cnocr_rec_model'),
                       det_model_name=self.settings.str('cnocr_det_model'))
        return engine.ocr(payload.path)
