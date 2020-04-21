'''
@Description: Capture than OCR - macOS - Online OCR
@version: 4.5
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
@LastEditTime: 2020-04-21 19:43:15
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

import config as c


ocr_select = int(sys.argv[1])
pic_path = sys.argv[2]
temp_path = '/private/tmp/com.chandler.alfredocr'

'''
Error Declare
'''


def declare_network_error():
    print('Network connection refused!', end='')
    sys.exit(0)

def declare_file_error():
    print('File ERROR!', end='')
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
        api_message = requests.get(c.BAIDU_GET_TOKEN_URL)
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
                url=c.BAIDU_OCR_API,
                params={
                    "access_token": return_baidu_token(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "image": convert_image_base64(pic_path),
                    "language_type": c.BAIDU_LANGUAGE_TYPE,
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


def baidu_ocr_qrcode(pic_path):
    if (os.path.getsize(pic_path) <= 4194304):
        try:
            response = requests.post(
                url=c.BAIDU_QRCODE_API,
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
                output_result(2, response_json)
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


def baidu_ocr_form(pic_path):
    if (os.path.getsize(pic_path) <= 4194304):
        try:
            response = requests.post(
                url=c.BAIDU_FORM_API,
                params={
                    "access_token": return_baidu_token(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "image": convert_image_base64(pic_path),
                    "is_sync": "true",
                    "request_type": "json",
                },
            )
            if (response.status_code == 200):
                response_json = response.json()['result']['result_data']
                response_json = json.loads(response_json)
                output_baidu_ocr_form(response_json)
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
    sign_text = parse.urlencode(dic) + '&app_key=' + c.TENCENT_YOUTU_APPKEY
    # MD5 + 转换大写
    sign = hashlib.md5(sign_text.encode('utf-8')).hexdigest().upper()
    return sign


def tencent_youtu_ocr(pic_path):
    if (1048576 <= os.path.getsize(pic_path) <= 4194304):
        baidu_ocr(pic_path)
        return
    elif (os.path.getsize(pic_path) <= 1048576):
        postdata = {'app_id': c.TENCENT_YOUTU_APPID, 'time_stamp': int(time.time()), 'nonce_str': ''.join(
            random.choices(string.ascii_letters + string.digits, k=8)), 'image': convert_image_base64(pic_path)}
        postdata['sign'] = request_tencent_youtu_sign(postdata, pic_path)
        try:
            response = requests.post(
                url=c.TENCENT_YOUTU_OCR_API,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data=postdata
            )
            if (response.status_code == 200):
                response_json = response.json()['data']['item_list']
                output_result(4, response_json)
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
    if c.GOOGLE_POST_REFERER:
        header['Referer'] = c.GOOGLE_POST_REFERER
    try:
        if c.GOOGLE_HTTP_PROXY:
            response = requests.post(
                url=c.GOOGLE_OCR_API,
                params={
                    "key": c.GOOGLE_ACCESS_TOKEN,
                },
                headers=header,
                data=data,
                proxies={
                    'http': 'http://' + c.GOOGLE_HTTP_PROXY,
                    'https': 'https://' + c.GOOGLE_HTTP_PROXY,
                }
            )
        else:
            response = requests.post(
                url=c.GOOGLE_OCR_API,
                params={
                    "key": c.GOOGLE_ACCESS_TOKEN,
                },
                headers=header,
                data=data
            )
        if (response.status_code == 200):
            response_json = response.json()['responses']
            output_result(5, response_json)
        else:
            print('Request failed!', end='')
    except requests.exceptions.ConnectionError:
        declare_network_error()


def multi_file_ocr():
    names = [name for name in os.listdir(temp_path)
             if re.search(r'.png|.jpg|.jpeg|.bmp', name, re.IGNORECASE) and os.path.getsize(temp_path + '/' + name) <= 4194304]
    for i in range(len(names)):
        current_pic_path = temp_path + '/' + names[i]
        baidu_ocr(current_pic_path)
        remove_pic(current_pic_path)
        if i != len(names) - 1:
            print('\n')


'''
Offline Barcode Decode (using !(zxing)[https://github.com/dlenski/python-zxing])
'''


def barcode_decode(pic_path):
    import zxing
    reader = zxing.BarCodeReader()
    barcode = reader.decode(pic_path)
    if barcode is not None:
        print(barcode.parsed, end='')
    else:
        print('Empty QR Code!')


'''
Output
'''


def output_result(which_api, result_json):
    if (which_api == 4):
        for index in range(len(result_json)):
            print(result_json[index]
                  ['itemstring'].replace(",", "，"), end='')
            if index != (len(result_json) - 1):
                print()
    elif (which_api == 5):
        text = result_json[0]['textAnnotations'][0]['description'].rstrip(
            '\n')
        print(text, end='')
    elif (which_api == 2):
        # 空二维码
        if (len(result_json) < 1):
            print('Empty QR Code!')
        # 单二维码
        elif (len(result_json) == 1):
            text_array = result_json[0]['text']
            for index in range(len(text_array)):
                print(text_array[index], end='')
                if index != (len(text_array) - 1):
                    print()
        # 多二维码
        else:
            for index_qrcode in range(len(result_json)):
                text_array = result_json[index_qrcode]['text']
                print('Group ' + str(index_qrcode + 1))
                for index_text in range(len(text_array)):
                    print(text_array[index_text], end='')
                    # 组内格式控制
                    if (index_qrcode != (len(result_json) - 1)):
                        print()
                # 组间格式控制
                if (index_qrcode != (len(result_json) - 1)):
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
        top_variance = c.BAIDU_OCR_SPACING_VARIANCE

    if top_variance >= c.BAIDU_OCR_SPACING_VARIANCE:
        is_line_spacing_check = 1
    else:
        is_line_spacing_check = 0

    for index in range(response_json['words_result_num']):
        line_width.append(
            response_json['words_result'][index]['location']['width'])
    try:
        width_half = statistics.median(line_width)
    except statistics.StatisticsError:
        print('Empty!', end='')
        sys.exit(0)

    for index in range(response_json['words_result_num']):
        words = response_json['words_result'][index]['words']
        if re.search(r'[\u4e00-\u9fa5+]', words):
            chinese_tag = 1
        else:
            chinese_tag = 0
        if chinese_tag == 1:
            is_num_between_chinese_space = re.finditer(
                r'[\u4e00-\u9fa5+][0-9a-zA-Z]', words)  # 汉字+数字
            if is_num_between_chinese_space != None:
                space_insert_offset = 0
                for i in is_num_between_chinese_space:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            is_num_between_space_chinese = re.finditer(
                r'[0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 数字+汉字
            if is_num_between_space_chinese != None:
                space_insert_offset = 0
                for i in is_num_between_space_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[1] + space_insert_offset - 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            words = words.replace(", ", "，").replace(",", "，")
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
        if (is_line_spacing_check == 1) and (index != response_json['words_result_num'] - 1) and (response_json['words_result'][index + 1]['location']['top'] - response_json['words_result'][index]['location']['top'] > top_half + c.BAIDU_OCR_SPACING_OFFSET):
            print()
        elif (is_line_spacing_check == 0) and (index != response_json['words_result_num'] - 1) and (response_json['words_result'][index]['location']['width'] < width_half - c.BAIDU_OCR_WIDTH_OFFSET):
            print()


def output_baidu_ocr_form(response_json):
    form_num = response_json['form_num']
    for i in range(form_num):
        column = response_json['forms'][i]['body'][-1]['column'][0]  # 当前表格列数
        row = response_json['forms'][i]['body'][-1]['row'][0]  # 当前表格行数
        form_array = [[0 for a in range(column)] for a in range(row)]
        form_body = response_json['forms'][i]['body']
        for j in range(len(response_json['forms'][i]['header'])):
            if response_json['forms'][i]['header'][j]['word'] != '':
                print(response_json['forms'][i]['header'][j]['word'], end='\t')
            if j != 0 or j != len(response_json['forms'][i]['header']) - 1:
                print()
        for j in range(len(form_body)):
            cell_col = form_body[j]['column'][0] - 1  # 当前单元格所在列
            cell_row = form_body[j]['row'][0] - 1  # 当前单元格所在行
            form_array[cell_row][cell_col] = form_body[j]['word']
        for k1 in range(cell_row + 1):
            for k2 in range(cell_col + 1):
                print(form_array[k1][k2], end='\t')
            if k1 != cell_row:
                print()


def remove_pic(pic_path):
    os.remove(pic_path)


if __name__ == "__main__":
    try:
        os.path.getsize(pic_path)
    except FileNotFoundError:
        declare_file_error()
    '''
    1: baidu
    2: baidu_qrcode
    3: baidu_form
    4: tencent
    5: google
    6: zxing
    7: file
    '''
    if (ocr_select == 1):
        baidu_ocr(pic_path)
    elif (ocr_select == 2):
        baidu_ocr_qrcode(pic_path)
    elif (ocr_select == 3):
        baidu_ocr_form(pic_path)
    elif (ocr_select == 4):
        tencent_youtu_ocr(pic_path)
    elif (ocr_select == 5):
        google_ocr(pic_path)
    elif (ocr_select == 6):
        barcode_decode(pic_path)
    elif (ocr_select == 7):
        multi_file_ocr()
    if (ocr_select != 7):
        remove_pic(pic_path)

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
