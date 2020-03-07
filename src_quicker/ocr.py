'''
@Description: Capture than OCR - Windows - Online OCR
@version: 1.0
@Author: Chandler Lu
@Date: 2020-03-07 17:38:10
@LastEditTime: 2020-03-07 22:16:23
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import statistics

import json
import re
import requests

import hashlib
import random
import string
from base64 import b64encode
from urllib import parse


ocr_select = int(sys.argv[1])
PIC_PATH = sys.argv[2]

# Control
BAIDU_OCR_SPACING_OFFSET = 8
BAIDU_OCR_SPACING_VARIANCE = 15
BAIDU_OCR_WIDTH_OFFSET = 50

# Key
with open("./API_Key.json", "r") as json_file:
    api_key = json.load(json_file)
BAIDU_API_KEY = api_key['baidu_api_key']
BAIDU_SECRET_KEY = api_key['baidu_secret_key']
TENCENT_YOUTU_APPID = api_key['tencent_youtu_appid']
TENCENT_YOUTU_APPKEY = api_key['tencent_youtu_appkey']
GOOGLE_ACCESS_TOKEN = api_key['google_access_token']
GOOGLE_POST_REFERER = api_key['google_post_referer']
GOOGLE_HTTP_PROXY = api_key['google_http_proxy']

# API
BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
    BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'
TENCENT_YOUTU_OCR_API = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'
GOOGLE_OCR_API = 'https://vision.googleapis.com/v1/images:annotate'


'''
Error Declare
'''


def declare_network_error():
    print('Network connection refused!', end='')
    sys.exit(0)


'''
Picture Convert
'''


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64


'''
Baidu OCR
'''


def request_baidu_token():
    try:
        api_message = requests.get(BAIDU_GET_TOKEN_URL)
        if api_message:
            with open("./baidu_api_token.json", "w") as json_file:
                json.dump(api_message.json(), json_file)
            token = api_message.json()['access_token']
            return token
    except requests.exceptions.ConnectionError:
        declare_network_error()


def return_baidu_token():
    if ((not os.path.exists('./baidu_api_token.json'))
            or (int(time.time() - os.stat("./baidu_api_token.json").st_mtime) >= 259200)):
        return request_baidu_token()
    else:
        with open("./baidu_api_token.json", 'r') as json_file:
            api_message_json = json.load(json_file)
            if 'access_token' in api_message_json:
                return api_message_json.get('access_token')
            else:
                return request_baidu_token()


def baidu_ocr(pic_path):
    if (os.path.getsize(pic_path) <= 4194304):
        try:
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
                output_baidu_ocr(response.json())
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


'''
Tencent Youtu OCR
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
    if (1048576 <= os.path.getsize(pic_path) <= 4194304):
        baidu_ocr(pic_path)
        return
    elif (os.path.getsize(pic_path) <= 1048576):
        postdata = {'app_id': TENCENT_YOUTU_APPID, 'time_stamp': int(time.time()), 'nonce_str': ''.join(
            random.choices(string.ascii_letters + string.digits, k=8)), 'image': convert_image_base64(pic_path)}
        postdata['sign'] = request_tencent_youtu_sign(postdata, pic_path)
        try:
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
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


'''
Google OCR
'''


def google_ocr(pic_path):
    header = {
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "requests": [
            {
                "image": {
                    "content": convert_image_base64(pic_path)
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    })
    if GOOGLE_POST_REFERER:
        header['Referer'] = GOOGLE_POST_REFERER
    try:
        if GOOGLE_HTTP_PROXY:
            response = requests.post(
                url=GOOGLE_OCR_API,
                params={
                    "key": GOOGLE_ACCESS_TOKEN,
                },
                headers=header,
                data=data,
                proxies={
                    'http': 'http://' + GOOGLE_HTTP_PROXY,
                    'https': 'https://' + GOOGLE_HTTP_PROXY,
                }
            )
        else:
            response = requests.post(
                url=GOOGLE_OCR_API,
                params={
                    "key": GOOGLE_ACCESS_TOKEN,
                },
                headers=header,
                data=data
            )
        if (response.status_code == 200):
            response_json = response.json()['responses']
            output_result('google_ocr', response_json)
        else:
            print('Request failed!', end='')
    except requests.exceptions.ConnectionError:
        declare_network_error()


'''
Output
'''


def output_result(which_api, result_json):
    response_json = result_json
    if (which_api is 'tencent_youtu_ocr'):
        for index in range(len(response_json)):
            print(response_json[index]
                  ['itemstring'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()
    elif (which_api is 'google_ocr'):
        text = response_json[0]['textAnnotations'][0]['description'].rstrip(
            '\n')
        print(text, end='')


def output_baidu_ocr(response_json):
    line_spacing = []
    line_width = []

    for index in range(response_json['words_result_num'] - 1):
        line_spacing.append(response_json['words_result'][index + 1]['location']
                            ['top'] - response_json['words_result'][index]['location']['top'])
    if line_spacing:
        top_half = statistics.median(line_spacing)
        top_variance = statistics.pvariance(line_spacing)
    else:
        top_half = 0
        top_variance = BAIDU_OCR_SPACING_VARIANCE

    if top_variance >= BAIDU_OCR_SPACING_VARIANCE:
        is_line_spacing_check = 1
    else:
        is_line_spacing_check = 0

    for index in range(response_json['words_result_num']):
        line_width.append(
            response_json['words_result'][index]['location']['width'])
    width_half = statistics.median(line_width)

    for index in range(response_json['words_result_num']):
        words = response_json['words_result'][index]['words']
        if re.search(r'[\u4e00-\u9fa5+]', words):
            chinese_tag = 1
        else:
            chinese_tag = 0
        if chinese_tag is 1:
            is_num_between_chinese = re.finditer(
                r'[\u4e00-\u9fa5+|\W][0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 测试666代码
            if is_num_between_chinese != None:
                space_insert_offset = 0  # 第一次插入空格后，后续插入点发生偏移
                for i in is_num_between_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    list_words.insert(i.span()[1] + space_insert_offset, ' ')
                    space_insert_offset += 2
                    words = ''.join(list_words)
            is_num_between_chinese_space = re.finditer(
                r'[\u4e00-\u9fa5+][0-9a-zA-Z]+( )+[\u4e00-\u9fa5+]', words)  # 测试666 代码
            if is_num_between_chinese_space != None:
                space_insert_offset = 0
                for i in is_num_between_chinese_space:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            is_num_between_space_chinese = re.finditer(
                r'( )+[0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 测试 666代码
            if is_num_between_space_chinese != None:
                space_insert_offset = 0
                for i in is_num_between_space_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[1] + space_insert_offset - 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            words = words.replace(", ", "，").replace(",", "，")
            # words = words.replace(". ", "。").replace(
            #     ".", "。").replace("。 ", "。")
            words = words.replace("!", "！")
            words = words.replace(";", "；")
            words = words.replace(":", "：")
            words = words.replace("(", "（")
            words = words.replace(")", "）")
            words = words.replace("?", "？")
            words = words.replace("—一", "——").replace("一—", "——")
            words = re.sub(r'( ){2,}', ' ', words)
            print(words, end='')
        else:
            words = words.replace("，", ",")
            words = words.replace("。", ".")
            words = words.replace("！", "!")
            words = words.replace("；", ";")
            words = words.replace("（", "(")
            words = words.replace("）", ")")
            words = words.replace("？", "?")
            words = re.sub(r'( ){2,}', ' ', words)
            print(words, end='')
        if (is_line_spacing_check is 1) and (index != response_json['words_result_num'] - 1) and (response_json['words_result'][index + 1]['location']['top'] - response_json['words_result'][index]['location']['top'] > top_half + BAIDU_OCR_SPACING_OFFSET):
            print()
        elif (is_line_spacing_check is 0) and (index != response_json['words_result_num'] - 1) and (response_json['words_result'][index]['location']['width'] < width_half - BAIDU_OCR_WIDTH_OFFSET):
            print()


def remove_pic(pic_path):
    os.remove(pic_path)


if __name__ == "__main__":
    '''
    1: baidu
    2: tencent
    3: google
    '''
    if (ocr_select == 1):
        baidu_ocr(PIC_PATH)
    elif (ocr_select == 2):
        tencent_youtu_ocr(PIC_PATH)
    elif (ocr_select == 3):
        google_ocr(PIC_PATH)
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
