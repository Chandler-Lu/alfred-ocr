'''
@Description: translate_caiyun
@version: 1.1
@Author: Chandler Lu
@Date: 2019-12-01 10:29:27
@LastEditTime: 2020-03-09 22:54:31
'''
# -*- coding: UTF-8 -*-
import sys
import os
import time
import re
import requests
import json

import config as c

translate_origin = sys.argv[1]


def caiyun_translate(chinese_tag, source):
    if (chinese_tag == 1):
        trans_type = 'zh2en'
    else:
        trans_type = 'auto2zh'
    response = requests.post(
        url=c.CAIYUN_TRANSLATE_API,
        headers={
            'Content-Type': 'application/json',
            'X-Authorization': 'token ' + c.CAIYUN_TRANSLATE_TOKEN,
        },
        data=json.dumps({
            "source": source,
            "request_id": str(time.time()),
            "trans_type": trans_type,
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
    if ((re.compile(u'[\u4e00-\u9fa5]+').search(translate_origin[0:8])) and (not re.compile(u'[\u0800-\u4dff]+').search(translate_origin[0:8]))):
        chinese_tag = 1
    else:
        chinese_tag = 0
    translate_result = caiyun_translate(chinese_tag, translate_origin)
    print(show_on_screen(translate_result, translate_origin))

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
