'''
@Description: Capture than OCR - Alfred for macOS - CNOCR
@version: 1.0
@Author: Chandler Lu
@Date: 2019-11-23 22:22:27
@LastEditTime: 2020-03-08 14:34:23
'''
# -*- coding: UTF-8 -*-
import sys
import os
from cnocr import CnOcr

pic_path = sys.argv[1]
ocr = CnOcr()
pic = ocr.ocr(pic_path)

for r in pic[:-1]:
    for c in r:
        print(c, end='')
    print()
for r in pic[-1]:
    for c in r:
        print(c, end='')

os.remove(pic_path)

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
