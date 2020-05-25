# Alfred - OCR and Translation

## Language

[简体中文][1] | English

## Download

[China-Mirror][2] | [Github-Release][3]

## OCR Demo

![][image-1]

## Feature

- Offline OCR (CNOCR)
- Online OCR (Baidu | Tencent Youtu | Google)
- QR Code Reader (Baidu | ZXing)
- Form OCR (Baidu)
- Multi File OCR (Baidu)
- Translate (ColorfulClouds)

## Installation

- You need install at least Alfred 3 or latest version and activate Powerpack;
- You need install Python 3 and necessary modules, then fill Python 3 Path at `PYTHON_PATH`;
- You need to apply and fill the configuration of the API Key into the environment variable;
- More installation details: [Install-Python(EN)][4]

## Python Module

### CNOCR

```bash
 pip install cnocr
```

### ZXing

```bash
 pip install zxing
```

### Others

```bash
 pip install requests
```

## Interfaces

### [CNOCR][5]

#### Trigger

- Use keyword `oo` to trigger screenshot selector.

#### Description

- More installation details: [README][6].

### [Baidu AI][7]

#### Trigger

1. Online OCR: Use shortcut key `ctrl + v` to trigger screenshot selector or Taking screenshot to clipboard then use keywords `oob (baidu)` to trigger.
2. QR Code Reader: Taking screenshot to clipboard then use keywords `ooqb (qr baidu)` to trigger.
3. Form OCR: Taking screenshot to clipboard then use keywords `ooe (excel)` to trigger, then you can copy it to Excel.
4. Multi File OCR: Select file in Finder and use keywords `oof (file)` to trigger.

![][image-2]

#### Description

1. QR Code support reading multiple at the same time;
2. The test token does not guarantee availability, you can apply for it if you need stability;
3. Single picture up to 4MB .

### [Tencent Youtu][8]

#### Trigger

- Online OCR: Taking screenshot to clipboard then use keywords `oot (tencent)` to trigger.

#### Description

1. The test token does not guarantee availability, you can apply for it if you need stability;
2. Single picture up to 1MB .

### [Google OCR][9]

#### Trigger

- Online OCR: Taking screenshot to clipboard then use keywords `oog (google)` to trigger.

#### Env Variable

| Name                | Description                                           |
| ------------------- | ----------------------------------------------------- |
| google\_access\_token | API Key                                               |
| google\_post\_referer | Referer parameter in HTTP request, default NULL       |
| google\_http\_proxy   | HTTP Proxy, default NULL. Reference: `127.0.0.1:1234` |

#### Description

- Google OCR is a fee-paying interfaces and requires a credit card. Therefore, this project does not have a test token. You must apply for it.

### [ZXing][10]

#### Trigger

- QR Code Reader: Taking screenshot to clipboard then use keywords `ooq` to trigger.

#### Description

1. More installation details: [README][11];
2. Only supports single QR code recognition.

## TODO

- Paragraph optimization.
- Screenshot translation.

## Thanks

1. [breezedeus/cnocr][12]
2. [dlenski/python-zxing][13]
3. [ginfuru/alfred-screen-capture][14]
4. [oott123/alfred-clipboard-ocr][15]
5. [Elvis Cai][16]

[1]:	https://github.com/Chandler-Lu/alfred-ocr/blob/master/README.md
[2]:	https://img.yeslu.cn/github/Capture_then_OCR.zip
[3]:	https://github.com/Chandler-Lu/alfred-ocr/releases "Github-Release"
[4]:	https://realpython.com/installing-python/#macos-mac-os-x
[5]:	https://github.com/breezedeus/cnocr
[6]:	https://github.com/breezedeus/cnocr/blob/master/README.md
[7]:	https://ai.baidu.com/tech/ocr
[8]:	https://ai.qq.com/product/ocr.shtml#common
[9]:	https://cloud.google.com/vision/docs/ocr
[10]:	https://github.com/dlenski/python-zxing
[11]:	https://github.com/dlenski/python-zxing/blob/master/README.md
[12]:	https://github.com/breezedeus/cnocr
[13]:	https://github.com/dlenski/python-zxing
[14]:	https://github.com/ginfuru/alfred-screen-capture
[15]:	https://github.com/oott123/alfred-clipboard-ocr
[16]:	https://github.com/elviscai

[image-1]:	examples/demo_ocr_en.gif
[image-2]:	examples/file_ocr.png