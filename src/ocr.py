'''
@Description: Capture then OCR - Alfred for macOS
@version: 4.9.5
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
LastEditTime: 2024-03-18 15:41:55
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
import hmac
import random
import string
from base64 import b64encode
from urllib import parse

import config as c
import tencent_ocr


ocr_select = int(sys.argv[1])
pic_path = sys.argv[2]
temp_path = '/private/tmp/com.chandler.alfredocr'

'''
Error Declare
'''


def declare_network_error():
    print('Error: Network connection refused!', end='')
    sys.exit(0)


def declare_file_error():
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
CNOCR: v2.3
https://github.com/breezedeus/CnOCR
'''


def cnocr_ocr(pic_path):
    if c.CNOCR_SERVE == 0:
        from cnocr import CnOcr
        ocr = CnOcr(rec_model_name='doc-densenet_lite_136-gru',
                    det_model_name='ch_PP-OCRv3_det')
        res = ocr.ocr(pic_path)
    elif c.CNOCR_SERVE == 1:
        try:
            req = requests.post(
                c.CNOCR_API, timeout=1.5, files={'image': (pic_path, open(pic_path, 'rb'))})
            res = req.json()['results']
        except requests.Timeout:
            print('Request timeout!', end='')
            sys.exit(0)
    for i in res:
        print(i['text'], end='')


'''
Baidu OCR
'''


def request_baidu_token():
    try:
        api_message = requests.get(c.BAIDU_GET_TOKEN_URL)
        if ('access_token' in api_message.json()):
            with open("./baidu_api_token.json", "w") as json_file:
                json.dump(api_message.json(), json_file)
            token = api_message.json()['access_token']
            return token
        else:
            print("Error: " + api_message.json()['error_description'], end='')
            sys.exit(0)
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
                if ('error_code' in response.json()):
                    print(response.json()['error_msg'])
                else:
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
                if ('error_code' in response.json()):
                    print(response.json()['error_msg'])
                else:
                    response_json = response.json()['codes_result']
                    output_result(2, response_json)
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


def baidu_ocr_table_process(d):
    # Initialize the table with empty strings
    max_row = max(item['row_start'] for item in d) + 1
    max_col = max(item['col_start'] for item in d) + 1
    table = [[""] * max_col for _ in range(max_row)]

    # Fill in the table with the data
    for item in d:
        row = item['row_start']
        col = item['col_start']
        words = item['words'].replace('\n', ' ')
        table[row][col] = words

    # Convert the table to a tab-separated string for display
    r = '\n'.join(['\t'.join(row) for row in table])
    return r


def baidu_ocr_table(pic_path):
    if (os.path.getsize(pic_path) <= 8388608):
        try:
            response = requests.post(
                url=c.BAIDU_TABLE_API,
                params={
                    "access_token": return_baidu_token(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "image": convert_image_base64(pic_path)
                },
            )
            if (response.status_code == 200):
                for table_index, table in enumerate(response.json()['tables_result']):
                    r = baidu_ocr_table_process(table['body'])
                    print(r)
                    print("\n")
            else:
                print('Request failed!', end='')
        except requests.exceptions.ConnectionError:
            declare_network_error()
    else:
        print('Too large!')


def baidu_ocr_formula(pic_path):
    if (os.path.getsize(pic_path) <= 4194304):
        try:
            response = requests.post(
                url=c.BAIDU_FORMULA_API,
                params={
                    "access_token": return_baidu_token(),
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "image": convert_image_base64(pic_path),
                    "disp_formula": "true"
                },
            )
            if (response.status_code == 200):
                result_num = response.json()['formula_result_num']
                if (result_num > 0):
                    response_json = response.json()['formula_result']
                    for i in range(result_num):
                        print(response_json[i]['words'], end=" \\\\")
                        if (i != result_num - 1):
                            print('\n')
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


'''
Mathpix OCR
'''


def mathpix_ocr(pic_path):
    ''' https://docs.mathpix.com/?python#request-parameters
    file_path = 'limit.jpg'
    image_uri = "data:image/jpg;base64," + b64encode(open(pic_path, "rb").read()).decode()
    r = requests.post("https://api.mathpix.com/v3/text",
                    data=json.dumps({'src': image_uri}),
                    headers={"app_id": "YOUR_APP_ID", "app_key": "YOUR_APP_KEY",
                            "Content-type": "application/json"})
    print(json.dumps(json.loads(r.text), indent=4, sort_keys=True))
    '''
    try:
        response = requests.post(
            url=c.MATHPIX_API,
            headers={
                'app_id': c.MATHPIX_APP_ID,
                'app_key': c.MATHPIX_APP_KEY,
                'Content-type': 'application/json',
            },
            data=json.dumps({
                'src': 'data:image/jpg;base64,' + convert_image_base64(pic_path)
            })
        )
        if (response.status_code == 200):
            if 'error' in response.json():
                print(response.json()['error'], end='')
            elif 'latex_styled' in response.json():
                print(response.json()['latex_styled'], end='')
            else:
                print(response.json()['text'], end='')
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
Offline Barcode Decode (using !(zxing-cpp)[https://github.com/zxing-cpp/zxing-cpp])
'''


def barcode_decode(pic_path):
    import cv2, zxingcpp
    img_qr = cv2.imread(pic_path)
    barcodes = zxingcpp.read_barcodes(img_qr)
    for barcode in barcodes:
        print(barcode.text)
    if len(barcodes) == 0:
        print('Empty QR Code!', end="")


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
            if is_num_between_chinese_space is not None:
                space_insert_offset = 0
                for i in is_num_between_chinese_space:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[0] + space_insert_offset + 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            is_num_between_space_chinese = re.finditer(
                r'[0-9a-zA-Z]+[\u4e00-\u9fa5+]', words)  # 数字+汉字
            if is_num_between_space_chinese is not None:
                space_insert_offset = 0
                for i in is_num_between_space_chinese:
                    list_words = list(words)
                    list_words.insert(
                        i.span()[1] + space_insert_offset - 1, ' ')
                    space_insert_offset += 1
                    words = ''.join(list_words)
            replace_map = {
                ", ": "，", ",": "，", "!": "！", ";": "；",
                ":": "：", "(": "（", ")": "）", "?": "？",
                "—一": "——", "一—": "——"
            }
        else:
            replace_map = {
                "，": ",", "。": ".", "！": "!", "；": ";",
                "（": "(", "）": ")", "？": "?"
            }
        for a, b in replace_map.items():
            words = words.replace(a, b)
        words = re.sub(r'( ){2,}', ' ', words)
        print(words, end="")
        if (is_line_spacing_check == 1) and (index != response_json['words_result_num'] - 1) and (
                response_json['words_result'][index + 1]['location']['top'] - response_json['words_result'][index]['location']['top'] > top_half + c.BAIDU_OCR_SPACING_OFFSET):
            print()
        elif (is_line_spacing_check == 0) and (index != response_json['words_result_num'] - 1) and (response_json['words_result'][index]['location']['width'] < width_half - c.BAIDU_OCR_WIDTH_OFFSET):
            print()


def remove_pic(pic_path):
    if os.path.isfile(pic_path):
        try:
            os.remove(pic_path)
            return True
        except Exception as e:
            return False
    else:
        return False


if __name__ == "__main__":
    ocr_functions = {
        0: cnocr_ocr,
        1: baidu_ocr,
        2: baidu_ocr_qrcode,
        3: baidu_ocr_table,
        4: tencent_ocr.tencent_ocr,
        5: google_ocr,
        6: barcode_decode,
        7: mathpix_ocr,
        8: baidu_ocr_formula,
        99: multi_file_ocr,
    }

    try:
        if ocr_select != 99:
            try:
                os.path.getsize(pic_path)
                ocr_functions[ocr_select](pic_path)
                remove_pic(pic_path)
            except FileNotFoundError:
                declare_file_error()
        else:
            ocr_functions[ocr_select]()
    except KeyError:
        print("Invalid API selector.")

'''
 ________
< rabbit >
 --------
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\
                ||----w |
                ||     ||
'''
