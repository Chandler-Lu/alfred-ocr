'''
@Description: ocr_baidu_google_tencent
@version: 2.0
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
@LastEditTime: 2019-12-05 21:54:10
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time

import json
import re
import requests

import hashlib
import random
import string
from base64 import b64encode
from urllib import parse


OCR_SELECT = sys.argv[1]
PIC_PATH = sys.argv[2]

# Key
BAIDU_API_KEY = os.environ["baidu_api_key"]
BAIDU_SECRET_KEY = os.environ["baidu_secret_key"]
TENCENT_YOUTU_APPID = os.environ["tencent_youtu_appid"]
TENCENT_YOUTU_APPKEY = os.environ["tencent_youtu_appkey"]

# API
BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
    BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
BAIDU_QRCODE_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/qrcode'
TENCENT_YOUTU_OCR_API = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64


'''
Baidu OCR Start
'''


def request_baidu_token():
    api_message = requests.get(BAIDU_GET_TOKEN_URL)
    if api_message:
        with open("./baidu_api_token.json", "w") as json_file:
            json.dump(api_message.json(), json_file)
        token = api_message.json().get('access_token')
        return token


def return_baidu_token():
    if ((not os.path.exists('./baidu_api_token.json'))
            or (int(time.time() - os.stat("./baidu_api_token.json").st_mtime) >= 259200)):
        return request_baidu_token()
    else:
        with open("./baidu_api_token.json", 'r') as json_file:
            api_message_JSON = json.load(json_file)
            if 'access_token' in api_message_JSON:
                return api_message_JSON.get('access_token')
            else:
                return request_baidu_token()


def baidu_ocr(pic_path):
    response = requests.post(
        url=BAIDU_OCR_API,
        params={
            "access_token": return_baidu_token(),
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "image": convert_image_base64(pic_path),
        },
    )
    if (response.status_code == 200):
        response_json = response.json()['words_result']
        output_result('baidu_ocr', response_json)
    else:
        print('Request failed!')


def baidu_ocr_qrcode(pic_path):
    response = requests.post(
        url=BAIDU_QRCODE_API,
        params={
            "access_token": return_baidu_token(),
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "image": convert_image_base64(pic_path),
        },
    )
    if (response.status_code == 200):
        response_json = response.json().get('codes_result')
        output_result('baidu_ocr_qrcode', response_json)
    else:
        print('Request failed!')


'''
Tencent Youtu OCR Start
'''


def request_tencent_youtu_sign(postdata, pic_path):
    # 字典升序排序
    dic = sorted(postdata.items(), key=lambda d: d[0])
    # URL编码 + 拼接app_key
    sign_text = parse.urlencode(dic) + '&app_key=' + TENCENT_YOUTU_APPKEY
    # MD5 + 转换大写
    sign = hashlib.md5(sign_text.encode('utf-8')).hexdigest().upper()
    return sign


def tencent_youtu_ocr(pic_path):
    if (os.path.getsize(pic_path) > 1048576 and os.path.getsize(pic_path) < 4194304):
        baidu_ocr(pic_path)
        return
    elif (os.path.getsize(pic_path) <= 1048576):
        postdata = {'app_id': TENCENT_YOUTU_APPID, 'time_stamp': int(time.time()), 'nonce_str': ''.join(
            random.choices(string.ascii_letters + string.digits, k=8)), 'image': convert_image_base64(pic_path)}
        postdata['sign'] = request_tencent_youtu_sign(postdata, pic_path)
        # 通知腾讯优图开始搞事
        response = requests.post(
            url=TENCENT_YOUTU_OCR_API,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data=postdata
        )
        if (response.status_code == 200):
            response_json = response.json()['data']['item_list']
            output_result('tencent_youtu_ocr', response_json)
        else:
            print('Request failed!')
    else:
        print('Too large!')


def output_result(which_api, result_json):
    response_json = result_json
    if (which_api is 'baidu_ocr'):
        for index in range(len(response_json)):
            if (re.search(r'[\u4e00-\u9fa5+]', response_json[index]['words'][0:10])):
                print(response_json[index]['words'].replace(
                    ",", "，").replace("!", "！").replace(";", "；").replace(":", "："), end='')
            else:
                print(response_json[index]['words'].replace(
                    "，", ", ").replace("！", "!").replace("；", "; ").replace("：", ":"), end='')
            if (index != (len(response_json) - 1)):
                if (not (re.search(r'[,|，|;|；]', response_json[index]['words'][-1])
                         or re.search(r'[,|，|.|。|;|；]', response_json[index + 1]['words'][0:5]))):
                    print()
    elif (which_api is 'baidu_ocr_qrcode'):
        # 空二维码
        if (len(response_json) < 1):
            print('Empty QR Code!')
        # 单二维码
        elif (len(response_json) == 1):
            text_array = response_json[0].get('text')
            for index in range(len(text_array)):
                print(text_array[index], end='')
                if index != (len(text_array) - 1):
                    print()
        # 多二维码
        else:
            for index_qrcode in range(len(response_json)):
                text_array = response_json[index_qrcode].get('text')
                print('Group ' + str(index_qrcode + 1))
                for index_text in range(len(text_array)):
                    print(text_array[index_text], end='')
                    # 组内格式控制
                    if (index_qrcode != (len(response_json) - 1)):
                        print()
                # 组间格式控制
                if (index_qrcode != (len(response_json) - 1)):
                    print()
    elif (which_api is 'tencent_youtu_ocr'):
        for index in range(len(response_json)):
            print(response_json[index]
                  ['itemstring'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()


def remove_pic(pic_path):
    os.remove(pic_path)


if __name__ == "__main__":
    if (OCR_SELECT == 'baidu'):
        baidu_ocr(PIC_PATH)
    elif (OCR_SELECT == 'tencent'):
        tencent_youtu_ocr(PIC_PATH)
    elif (OCR_SELECT == 'baidu_qrcode'):
        baidu_ocr_qrcode(PIC_PATH)
    remove_pic(PIC_PATH)

'''
 ________
< rabbit >
 --------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
'''
