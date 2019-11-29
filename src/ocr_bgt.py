'''
@Description: ocr_baidu_google_tencent
@version: 2.6
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
@LastEditTime: 2019-11-29 21:56:46
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import requests
import json
from base64 import b64encode

OCR_SELECT = sys.argv[1]
PIC_PATH = sys.argv[2]
baidu_api_key = os.environ["baidu_api_key"]
baidu_secret_key = os.environ["baidu_secret_key"]
tencent_youtu_appid = os.environ["tencent_youtu_appid"]
tencent_youtu_appkey = os.environ["tencent_youtu_appkey"]


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64


'''
Baidu OCR Start
'''


def request_baidu_token():
    baidu_get_token_url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
        baidu_api_key + '&client_secret=' + baidu_secret_key
    api_message = requests.get(baidu_get_token_url)
    if api_message:
        with open("./baidu_api_token.json", "w") as json_file:
            json.dump(api_message.json(), json_file)
            json_file.close()
        token = api_message.json().get('access_token')
        return token


def return_baidu_token():
    if ((not os.path.exists('./baidu_api_token.json')) or (int(time.time() - os.stat("./baidu_api_token.json").st_mtime) >= 259200)):
        return request_baidu_token()
    else:
        with open("./baidu_api_token.json", 'r') as json_file:
            api_message_JSON = json.load(json_file)
            if 'access_token' in api_message_JSON:
                return api_message_JSON.get('access_token')
            else:
                return request_baidu_token()


def baidu_ocr(pic_path):
    baidu_ocr_api = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
    response = requests.post(
        url=baidu_ocr_api,
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
        response_json = response.json().get('words_result')
        for index in range(len(response_json)):
            print(response_json[index]['words'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()
    else:
        print('Request failed!')


'''
Tencent Youtu OCR Start
'''


def request_tencent_youtu_sign(postdata, pic_path):
    import hashlib
    from urllib import parse
    # 字典升序排序
    dic = sorted(postdata.items(), key=lambda d: d[0])
    # URL编码 + 拼接app_key
    sign_text = parse.urlencode(dic) + '&app_key=' + tencent_youtu_appkey
    # MD5 + 转换大写
    sign = hashlib.md5(sign_text.encode('utf-8')).hexdigest().upper()
    return sign


def tencent_youtu_ocr(pic_path):
    import random
    import string
    tencent_youtu_ocr_api = 'https://api.ai.qq.com/fcgi-bin/ocr/ocr_generalocr'
    postdata = {'app_id': tencent_youtu_appid, 'time_stamp': int(time.time()), 'nonce_str': ''.join(
        random.choices(string.ascii_letters + string.digits, k=8)), 'image': convert_image_base64(pic_path)}
    postdata['sign'] = request_tencent_youtu_sign(postdata, pic_path)
    # 通知腾讯优图开始搞事
    response = requests.post(
        url=tencent_youtu_ocr_api,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=postdata
    )
    if (response.status_code == 200):
        response_json = response.json().get('data').get('item_list')
        for index in range(len(response_json)):
            print(response_json[index]['itemstring'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()
    else:
        print('Request failed!')


def remove_pic(pic_path):
    os.remove(pic_path)


if __name__ == "__main__":
    if (OCR_SELECT == 'baidu'):
        baidu_ocr(PIC_PATH)
    elif (OCR_SELECT == 'tencent'):
        tencent_youtu_ocr(PIC_PATH)
    remove_pic(PIC_PATH)
