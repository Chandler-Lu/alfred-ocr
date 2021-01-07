'''
Description:
version:
Author: Chandler Lu
Date: 2021-01-07 16:47:12
LastEditTime: 2021-01-07 17:25:26
'''

import os
import time
from datetime import datetime
import requests
import hashlib
import json
import hmac

import config as c
import img_to_b64
import error_declare


def tencent_sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def tencent_ocr(pic_path):
    if (os.path.getsize(pic_path) <= 3145728):
        # 请求方式
        tencent_http_request_method = 'POST'
        tencent_canonical_uri = '/'
        tencent_canonical_query_string = ''
        tencent_canonical_headers = "content-type:%s\nhost:%s\n" % (
            c.TENCENT_CONTENT_TYPE, c.TENCENT_OCR_HOST)
        tencent_signed_headers = 'content-type;host'

        # 签名方式
        tencent_algorithm = 'TC3-HMAC-SHA256'

        # 时间戳
        tencent_request_timestamp = int(time.time())
        tencent_request_date = str(datetime.utcfromtimestamp(
            tencent_request_timestamp).strftime("%Y-%m-%d"))

        # 参数准备
        tencent_credential_scope_data = [
            tencent_request_date, c.TENCENT_SERVICE, 'tc3_request']
        tencent_credential_scope = '/'.join(tencent_credential_scope_data)

        # 图片数据
        data_img = {
            "ImageBase64": img_to_b64.convert_image_base64(pic_path)
        }
        data_img = json.dumps(data_img).encode('utf-8')
        tencent_hashed_request_payload = hashlib.sha256(
            data_img).hexdigest().lower()

        # 规范请求串
        tencnet_canonical_request_data = [
            tencent_http_request_method,
            tencent_canonical_uri,
            tencent_canonical_query_string,
            tencent_canonical_headers,
            tencent_signed_headers,
            tencent_hashed_request_payload]
        tencnet_canonical_request = '\n'.join(tencnet_canonical_request_data)
        tencent_hashed_canonical_request = hashlib.sha256(
            tencnet_canonical_request.encode("utf-8")).hexdigest()

        # 待签名字符串
        tencent_string_to_sign_data = [
            tencent_algorithm,
            str(tencent_request_timestamp),
            tencent_credential_scope,
            tencent_hashed_canonical_request]
        tencent_string_to_sign = '\n'.join(tencent_string_to_sign_data)

        # 计算签名
        tencent_secret_date = tencent_sign(
            ("TC3" + c.TENCENT_SECRET_KEY).encode("utf-8"),
            tencent_request_date)
        tencent_secret_service = tencent_sign(
            tencent_secret_date, c.TENCENT_SERVICE)
        tencent_secret_signing = tencent_sign(
            tencent_secret_service, "tc3_request")
        tencent_signature = hmac.new(
            tencent_secret_signing,
            tencent_string_to_sign.encode("utf-8"),
            hashlib.sha256).hexdigest()

        tencent_authorization = tencent_algorithm + ' ' + 'Credential=' + c.TENCENT_SECRET_ID + '/' + \
            tencent_credential_scope + ', ' + 'SignedHeaders=' + \
            tencent_signed_headers + ', ' + 'Signature=' + tencent_signature

        try:
            response = requests.post(
                url=c.TENCENT_OCR_API,
                headers={
                    "Content-Type": c.TENCENT_CONTENT_TYPE,
                    "X-TC-Action": c.TENCENT_ACTION,
                    "X-TC-Region": "ap-shanghai",
                    "X-TC-Timestamp": str(tencent_request_timestamp),
                    "X-TC-Version": "2018-11-19",
                    "Authorization": tencent_authorization,
                },
                data=data_img,
            )
            if (response.status_code == 200):
                if 'Error' in response.json()['Response']:
                    print(response.json()['Response']['Error']['Message'])
                else:
                    output(response.json()['Response']['TextDetections'])
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


def output(message):
    for i in range(len(message)):
        print(message[i]['DetectedText'], end='')
        if i != len(message) - 1:
            print()
