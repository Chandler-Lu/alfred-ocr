# -*- coding: UTF-8 -*-
import sys
import os
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


def get_baidu_token():
    baidu_get_token_url = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + \
        baidu_api_key + '&client_secret=' + baidu_secret_key
    response = requests.get(baidu_get_token_url)
    if response:
        token = response.json().get('access_token')
        return token


def baidu_ocr():
    baidu_ocr_api = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
    try:
        response = requests.post(
            url=baidu_ocr_api,
            params={
                "access_token": get_baidu_token(),
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
