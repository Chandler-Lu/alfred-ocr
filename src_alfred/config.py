'''
@Description: Capture than OCR - Variable
@version: 1.0
@Author: Chandler Lu
@Date: 2020-03-09 20:32:15
@LastEditTime: 2020-03-09 23:31:02
'''
# -*- coding: UTF-8 -*-

import os

# Control
BAIDU_OCR_SPACING_OFFSET = 8
BAIDU_OCR_SPACING_VARIANCE = 15
BAIDU_OCR_WIDTH_OFFSET = 50

# Key - Alfred
BAIDU_API_KEY = os.environ['baidu_api_key']
BAIDU_SECRET_KEY = os.environ['baidu_secret_key']
TENCENT_YOUTU_APPID = os.environ['tencent_youtu_appid']
TENCENT_YOUTU_APPKEY = os.environ['tencent_youtu_appkey']
GOOGLE_ACCESS_TOKEN = os.environ['google_access_token']
GOOGLE_POST_REFERER = os.environ['google_post_referer']
GOOGLE_HTTP_PROXY = os.environ['google_http_proxy']
CAIYUN_TRANSLATE_TOKEN = os.environ['caiyun_token']

# Key - Quicker

# BAIDU_API_KEY = 'rmMynojL9KapDOikDTgKlImy'
# BAIDU_SECRET_KEY = '3QKoI1E56u16tEMdwBnpXSPNezdoZWFD'
# TENCENT_YOUTU_APPID = '2124810247'
# TENCENT_YOUTU_APPKEY = 'OUd1lpQk4yqp9vSs'
# GOOGLE_ACCESS_TOKEN = ''
# GOOGLE_POST_REFERER = ''
# GOOGLE_HTTP_PROXY = ''
# CAIYUN_TRANSLATE_TOKEN = '3975l6lr5pcbvidl6jl2'

# API
BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
    BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'
BAIDU_QRCODE_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/qrcode'
BAIDU_FORM_API = 'https://aip.baidubce.com/rest/2.0/solution/v1/form_ocr/request'
TENCENT_YOUTU_OCR_API = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'
GOOGLE_OCR_API = 'https://vision.googleapis.com/v1/images:annotate'
CAIYUN_TRANSLATE_API = 'http://api.interpreter.caiyunai.com/v1/translator'