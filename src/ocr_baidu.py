'''
@Description: ocr_baidu
@version: 2.5
@Author: Chandler Lu
@Date: 2019-11-26 23:52:36
@LastEditTime: 2019-11-28 23:11:51
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import requests
import json
from base64 import b64encode

pic_path = sys.argv[1]
baidu_api_key = os.environ["baidu_api_key"]
baidu_secret_key = os.environ["baidu_secret_key"]


def convert_image_base64():
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64


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
    if (not os.path.exists('./baidu_api_token.json') or (int(time.time() - os.stat("./baidu_api_token.json").st_mtime) >= 259200)):
        return request_baidu_token()
    else:
        with open("./baidu_api_token.json", 'r') as json_file:
            api_message_JSON = json.load(json_file)
            if 'access_token' in api_message_JSON:
                return api_message_JSON.get('access_token')
            else:
                return request_baidu_token()


def baidu_ocr():
    baidu_ocr_api = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
    try:
        response = requests.post(
            url=baidu_ocr_api,
            params={
                "access_token": return_baidu_token(),
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "image": convert_image_base64(),
            },
        )
        response_json = response.json().get('words_result')
        for index in range(len(response_json)):
            print(response_json[index]['words'].replace(",", "，"), end='')
            if index != (len(response_json) - 1):
                print()
    except requests.exceptions.RequestException:
        print('Request failed!')


def remove_pic():
    os.remove(pic_path)


baidu_ocr()
remove_pic()
