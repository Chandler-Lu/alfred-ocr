'''
@Description: ocr_baidu_google_tencent
@version: 3.1
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
@LastEditTime : 2019-12-24 10:13:37
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


OCR_SELECT = sys.argv[1]
PIC_PATH = sys.argv[2]
FOLDER_PATH = '/private/tmp/com.chandler.alfredocr'

# Control
BAIDU_OCR_SPACING_OFFSET = 8
BAIDU_OCR_SPACING_VARIANCE = 15
BAIDU_OCR_WIDTH_OFFSET = 50

# Key
BAIDU_API_KEY = os.environ["baidu_api_key"]
BAIDU_SECRET_KEY = os.environ["baidu_secret_key"]
TENCENT_YOUTU_APPID = os.environ["tencent_youtu_appid"]
TENCENT_YOUTU_APPKEY = os.environ["tencent_youtu_appkey"]
GOOGLE_ACCESS_TOKEN = os.environ["google_access_token"]
GOOGLE_POST_REFERER = os.environ["google_post_referer"]
GOOGLE_HTTP_PROXY = os.environ["google_http_proxy"]

# API
BAIDU_GET_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
    BAIDU_API_KEY + '&client_secret=' + BAIDU_SECRET_KEY
BAIDU_OCR_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'
BAIDU_QRCODE_API = 'https://aip.baidubce.com/rest/2.0/ocr/v1/qrcode'
TENCENT_YOUTU_OCR_API = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'
GOOGLE_OCR_API = 'https://vision.googleapis.com/v1/images:annotate'


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64


'''
Baidu OCR
'''


def request_baidu_token():
    api_message = requests.get(BAIDU_GET_TOKEN_URL)
    if api_message:
        with open("./baidu_api_token.json", "w") as json_file:
            json.dump(api_message.json(), json_file)
        token = api_message.json()['access_token']
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
    if (os.path.getsize(pic_path) <= 4194304):
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
    else:
        print('Too large!')


def baidu_ocr_qrcode(pic_path):
    if (os.path.getsize(pic_path) <= 4194304):
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
            response_json = response.json()['codes_result']
            output_result('baidu_qrcode', response_json)
        else:
            print('Request failed!', end='')
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
    else:
        print('Too large!')


'''
Google OCR
'''


def google_ocr(pic_path):
    header = {
        "Content-Type": "application/json",
    }
    if GOOGLE_POST_REFERER:
        header['Referer'] = GOOGLE_POST_REFERER
    if GOOGLE_HTTP_PROXY:
        response = requests.post(
            url="https://vision.googleapis.com/v1/images:annotate",
            params={
                "key": GOOGLE_ACCESS_TOKEN,
            },
            headers=header,
            data=json.dumps({
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
            }),
            proxies={
                'http': 'http://' + GOOGLE_HTTP_PROXY,
                'https': 'https://' + GOOGLE_HTTP_PROXY,
            }
        )
    else:
        response = requests.post(
            url="https://vision.googleapis.com/v1/images:annotate",
            params={
                "key": GOOGLE_ACCESS_TOKEN,
            },
            headers={
                "Content-Type": "application/json",
                "Referer": GOOGLE_POST_REFERER,
            },
            data=json.dumps({
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
        )
    if (response.status_code == 200):
        response_json = response.json()['responses']
        output_result('google_ocr', response_json)
    else:
        print('Request failed!', end='')


def multi_file_ocr():
    names = [name for name in os.listdir(FOLDER_PATH)
             if re.search(r'.png|.jpg|.jpeg|.bmp', name, re.IGNORECASE) and os.path.getsize(FOLDER_PATH + '/' + name) <= 4194304]
    for i in range(len(names)):
        current_pic_path = FOLDER_PATH + '/' + names[i]
        baidu_ocr(current_pic_path)
        remove_pic(current_pic_path)
        if i != len(names) - 1:
            print('\n')


'''
Output
'''


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
    elif (which_api is 'tencent_youtu_ocr'):
        for index in range(len(response_json)):
            print(response_json[index]
                  ['itemstring'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()
    elif (which_api is 'google_ocr'):
        text = response_json[0]['textAnnotations'][0]['description'].rstrip(
            '\n')
        print(text, end='')
    elif (which_api is 'baidu_qrcode'):
        # 空二维码
        if (len(response_json) < 1):
            print('Empty QR Code!')
        # 单二维码
        elif (len(response_json) == 1):
            text_array = response_json[0]['text']
            for index in range(len(text_array)):
                print(text_array[index], end='')
                if index != (len(text_array) - 1):
                    print()
        # 多二维码
        else:
            for index_qrcode in range(len(response_json)):
                text_array = response_json[index_qrcode]['text']
                print('Group ' + str(index_qrcode + 1))
                for index_text in range(len(text_array)):
                    print(text_array[index_text], end='')
                    # 组内格式控制
                    if (index_qrcode != (len(response_json) - 1)):
                        print()
                # 组间格式控制
                if (index_qrcode != (len(response_json) - 1)):
                    print()


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
                r'[\u4e00-\u9fa5+][0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 测试666代码
            is_num_between_chinese_space = re.finditer(
                r'[\u4e00-\u9fa5+][0-9a-zA-Z]+( )+[\u4e00-\u9fa5+]', words)  # 测试666 代码
            is_num_between_space_chinese = re.finditer(
                r'( )+[0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 测试 666代码
            if is_num_between_chinese != None:
                space_insert_offset = 0  # 第一次插入空格后，后续插入点发生偏移
                for i in is_num_between_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    list_words.insert(i.span()[1] + space_insert_offset, ' ')
                    space_insert_offset += 2
                    words = ''.join(list_words)
            if is_num_between_chinese_space != None:
                space_insert_offset = 0
                for i in is_num_between_chinese_space:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            if is_num_between_space_chinese != None:
                space_insert_offset = 0
                for i in is_num_between_space_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[1] + space_insert_offset - 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            words = words.replace(", ", "，").replace(",", "，")
            words = words.replace(". ", "。").replace(
                ".", "。").replace("。 ", "。")
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
    if (OCR_SELECT == 'baidu'):
        baidu_ocr(PIC_PATH)
        remove_pic(PIC_PATH)
    elif (OCR_SELECT == 'tencent'):
        tencent_youtu_ocr(PIC_PATH)
        remove_pic(PIC_PATH)
    elif (OCR_SELECT == 'google'):
        google_ocr(PIC_PATH)
        remove_pic(PIC_PATH)
    elif (OCR_SELECT == 'baidu_qrcode'):
        baidu_ocr_qrcode(PIC_PATH)
        remove_pic(PIC_PATH)
    elif (OCR_SELECT == 'file'):
        multi_file_ocr()

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
