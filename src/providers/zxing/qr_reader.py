'''Offline barcode and QR decoding.

https://github.com/zxing-cpp/zxing-cpp
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from core.base_provider import BaseProvider, OcrResult
from core.exceptions import DependencyError, EmptyResultError, ImageError
from core.image_loader import ImageFile


class ZxingQrReader(BaseProvider):
    name = 'zxing'
    aliases = ('ooq', 'barcode')
    selector = 6
    summary = 'Offline barcode / QR decoding via zxing-cpp'

    def recognize(self, payload: ImageFile) -> OcrResult:
        try:
            import cv2
            import zxingcpp
        except ImportError as error:
            raise DependencyError(
                'Error: zxing-cpp / opencv is not installed!') from error

        image = cv2.imread(payload.path)
        if image is None:
            raise ImageError('Error: image unreadable!')
        barcodes = zxingcpp.read_barcodes(image)
        if not barcodes:
            raise EmptyResultError('Empty QR Code!')
        # A barcode payload is data, not prose: emit it verbatim.
        return OcrResult.raw('\n'.join(barcode.text for barcode in barcodes))
