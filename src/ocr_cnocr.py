# -*- coding: UTF-8 -*-
import sys
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
