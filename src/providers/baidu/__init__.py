'''Baidu AI open platform: general text, tables, QR codes and formulas.'''

from providers.baidu.formula_ocr import BaiduFormulaOcr
from providers.baidu.general_ocr import BaiduGeneralOcr, BaiduMultiFileOcr
from providers.baidu.qr_reader import BaiduQrReader
from providers.baidu.table_ocr import BaiduTableOcr

__all__ = ['BaiduFormulaOcr', 'BaiduGeneralOcr', 'BaiduMultiFileOcr',
           'BaiduQrReader', 'BaiduTableOcr']
