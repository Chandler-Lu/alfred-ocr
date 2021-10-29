'''
@Description: Capture than OCR - Variable
@Author: Chandler Lu
@Date: 2020-03-09 20:32:15
LastEditTime: 2021-01-07 17:29:41
'''
# -*- coding: UTF-8 -*-
import os

# Key - Alfred
BAIDU_API_KEY = os.environ['baidu_api_key']
BAIDU_SECRET_KEY = os.environ['baidu_secret_key']
if os.environ['baidu_language_type'] == '':
    BAIDU_LANGUAGE_TYPE = 'CHN_ENG'
else:
    BAIDU_LANGUAGE_TYPE = os.environ['baidu_language_type']
TENCENT_SECRET_ID = os.environ['tencent_secret_id']
TENCENT_SECRET_KEY = os.environ['tencent_secret_key']
GOOGLE_ACCESS_TOKEN = os.environ['google_access_token']
GOOGLE_POST_REFERER = os.environ['google_post_referer']
GOOGLE_HTTP_PROXY = os.environ['google_http_proxy']
CAIYUN_TRANSLATE_TOKEN = os.environ['caiyun_token']
MATHPIX_APP_ID = os.environ['mathpix_app_id']
MATHPIX_APP_KEY = os.environ['mathpix_app_key']

# Key - Quicker

# BAIDU_API_KEY = 'rmMynojL9KapDOikDTgKlImy'
# BAIDU_SECRET_KEY = '3QKoI1E56u16tEMdwBnpXSPNezdoZWFD'
# TENCENT_SECRET_ID = ''
# TENCENT_SECRET_KEY = ''
# # GOOGLE_ACCESS_TOKEN = ''
# GOOGLE_POST_REFERER = ''
# GOOGLE_HTTP_PROXY = ''
# CAIYUN_TRANSLATE_TOKEN = '3975l6lr5pcbvidl6jl2'
# MATHPIX_APP_ID = ''
# MATHPIX_APP_KEY = ''

# API
BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
    BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'
BAIDU_QRCODE_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/qrcode'
BAIDU_FORM_API = 'https://aip.baidubce.com/rest/2.0/solution/v1/form_ocr/request'
GOOGLE_OCR_API = 'https://vision.googleapis.com/v1/images:annotate'
CAIYUN_TRANSLATE_API = 'http://api.interpreter.caiyunai.com/v1/translator'
MATHPIX_API = 'https://api.mathpix.com/v3/text'

# Tencent Control
TENCENT_SERVICE = 'ocr'
TENCENT_ACTION = 'GeneralFastOCR'
TENCENT_OCR_HOST = 'ocr.tencentcloudapi.com'
TENCENT_OCR_API = 'https://ocr.tencentcloudapi.com'
TENCENT_CONTENT_TYPE = 'application/json; charset=utf-8'

# Baidu Control
BAIDU_OCR_SPACING_OFFSET = 8
BAIDU_OCR_SPACING_VARIANCE = 15
BAIDU_OCR_WIDTH_OFFSET = 50
