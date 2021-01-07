'''
Description: Convert IMG to BASE64
Author: Chandler Lu
Date: 2021-01-07 16:57:01
LastEditTime: 2021-01-07 17:09:50
'''
from base64 import b64encode


def convert_image_base64(pic_path):
    with open(pic_path, 'rb') as pic_file:
        byte_content = pic_file.read()
        pic_base64 = b64encode(byte_content).decode('utf-8')
        return pic_base64
