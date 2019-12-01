'''
@Description: translate_caiyun
@version: 1.0
@Author: Chandler Lu
@Date: 2019-12-01 10:29:27
@LastEditTime: 2019-12-01 21:27:17
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import requests
import json

translate_origin = sys.argv[1]

# API
caiyun_translate_token = os.environ["caiyun_token"]

# Key
caiyun_translate_api = "http://api.interpreter.caiyunai.com/v1/translator"


def caiyun_translate(source):
    response = requests.post(
        url=caiyun_translate_api,
        headers={
            "Content-Type": "application/json",
            "X-Authorization": "token " + caiyun_translate_token,
        },
        data=json.dumps({
            "source": source,
            "request_id": str(time.time()),
            "trans_type": "auto2zh",
            "detect": "True"
        })
    )
    return response.json().get('target')


def show_on_screen(title, subtitle):
    screen_data = {"items": [
        {
            "type": "default",
            "title": translate_result,
            "subtitle": translate_origin,
            "text": {
                "copy": translate_result,
            }
        }
    ]}
    screen_data = json.dumps(screen_data)
    return screen_data


if __name__ == "__main__":
    translate_result = caiyun_translate(translate_origin)
    print(show_on_screen(translate_result, translate_origin))
