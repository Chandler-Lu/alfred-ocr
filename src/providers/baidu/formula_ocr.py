'''Baidu formula recognition, emitted as LaTeX.'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from core.base_provider import BaseProvider, OcrResult
from core.image_loader import ImageFile
from providers.baidu import client


class BaiduFormulaOcr(BaseProvider):
    name = 'baidu-formula'
    aliases = ('formula', 'oobf')
    selector = 8
    summary = 'Baidu formula recognition (LaTeX)'
    required_credentials = ('baidu_api_key', 'baidu_secret_key')
    max_bytes_setting = 'baidu_max_image_bytes'

    def recognize(self, payload: ImageFile) -> OcrResult:
        response = client.request('baidu_formula_api', payload, self.max_bytes,
                                  {'disp_formula': 'true'})
        formulas = [str(item.get('words', '')).strip()
                    for item in response.get('formula_result') or []]
        # LaTeX must survive untouched, hence raw(); \\ ends a display line.
        return OcrResult.raw('\n\n'.join(
            formula + ' \\\\' for formula in formulas if formula)).or_raise()
