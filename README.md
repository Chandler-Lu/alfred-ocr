# Alfred Workflow - OCR and Translation

> 觉得好用的请点个 star，谢谢～

## 下载地址

[国内直链](http://bz.cndzq.com/ltr970503/3_software/2_tool/Capture%20then%20OCR.zip) 或 [Github Release](https://github.com/Chandler-Lu/alfred-ocr/releases)

## OCR Demo

![Demo_OCR](examples/demo_ocr.gif)

## Translate Demo

![Demo_Trans](examples/demo_trans.gif)

## 版本

> 4.0 版本发布后，除严重 Bug 的修复和功能新增外，将不会发布 Release，仅更新源码。

[查看更新历史](https://github.com/Chandler-Lu/alfred-ocr/wiki/Update-History)

### 4.2 (2020-01-16 12:54)

- 鉴于百度更改了二维码识别收费方案，触发关键词 `ooq` 替换为由开源模块 [ZXing](https://github.com/dlenski/python-zxing) 的二维码识别，原有百度二维码识别的触发方式更改为 `ooqb`。

## 能力

- 离线 OCR (CNOCR)
- 通用 OCR (百度，腾讯优图，Google)
- 二维码识别 (百度，ZXing)
- 表格文字识别 (百度)
- 多文件识别 (百度)
- 文本翻译 (彩云小译)

## 使用（必看！！）

1. 这**不是**一个开箱即用的产品！
2. 您至少要拥有 macOS Alfred 3 及以上版本并激活 Powerpack。
3. 您需要安装 Python 3 及相应的依赖模块，并将 Python 3 路径填写在`PYTHON_PATH`处。
4. 您需要申请并将对应接口的配置填入环境变量，部分接口附带我自己的 Key，但严禁滥用。
5. 具体配置方法请移步 [Q&A](https://github.com/Chandler-Lu/alfred-ocr/wiki/Q&A)。

### 设置方式

![env_button](examples/env_button.png)
![env_value](examples/env_value.png)

## 依赖

### CNOCR

``` bash
pip install cnocr
```

### ZXing (QR code Offline)

``` bash
pip install zxing
```

### 其他

``` bash
pip install requests
```

## 接口

### [CNOCR](https://github.com/breezedeus/cnocr)

#### 触发

1. 通用 OCR：使用关键词 oo 触发截图选框。

#### 说明

1. 一切安装方法请依据该项目 [README](https://github.com/breezedeus/cnocr/blob/master/README.md)。

### [Baidu AI (百度)](https://ai.baidu.com/tech/ocr)

#### 触发

1. 通用 OCR：快捷键 ctrl+v 触发截图选框，或截图至剪贴板后使用关键词 oob (baidu) 触发。
2. 二维码识别：截图后使用关键词 ooqb (qr baidu) 触发。
3. 表格文字识别：截图后使用关键词 ooe (excel) 触发，识别后可直接复制至 Excel。
4. 多文件识别：finder 中选中需要识别的图片并使用关键词 oof (file) 触发。

![File_OCR](examples/file_ocr.png)

#### 说明

1. 具备中英文识别，标点符号将被替换为对应语言下的符号。
2. 具备对出版物的段落优化能力，但对于非常规文本的分段能力并不是很好，等待进一步优化。
3. 二维码识别支持同时识别多个。
4. 自带一个测试 Token，不保证可用性，需要稳定可自行申请。
5. 最大支持单个 4MB 的图片。

### [Tencent Youtu (腾讯优图)](https://ai.qq.com/product/ocr.shtml#common)

#### 触发

1. 通用 OCR：截图至剪贴板后使用关键词 oot (tencent) 触发。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请。
2. 最大支持 1MB 的图片，过大图片会自动交由百度处理（当然百度最大也只支持 4MB）。

### [Google OCR](https://cloud.google.com/vision/docs/ocr)

#### 触发

1. 通用 OCR：截图至剪贴板后使用关键词 oog (google) 触发。

#### 环境变量

| 变量名              | 字段说明                                         |
| ------------------- | ------------------------------------------------ |
| google_access_token | 授权密钥                                         |
| google_post_referer | HTTP 请求时的 Referer 参数，默认为空             |
| google_http_proxy   | HTTP 代理，默认为空，填写方式如 `127.0.0.1:1234` |

#### 说明

1. Google OCR 为收费业务，需绑定信用卡，故本项目不带测试 Token，需要自行申请。

### [ZXing](https://github.com/dlenski/python-zxing) (离线二维码识别)

#### 触发

1. 截图至剪贴板后使用关键词 ooq (qr code) 触发。

#### 说明

1. 一切安装方法请依据该项目 [README](https://github.com/dlenski/python-zxing/blob/master/README.md)。
2. 仅支持单个二维码识别。

### [ColorfulClouds (彩云小译)](https://fanyi.caiyunapp.com/#/api)

#### 触发

1. 文本翻译：使用关键词 tc (translate caiyun) + 需要翻译的内容来触发；输出结果可通过 command + v 复制。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请。
2. 支持中译英，及 X 译中(X 为彩云小译已经支持的语言类别)。

## 说明

- 虽然已经有很多大佬做过类似的 workflow，但是依然存在一些痛点没能解决；而作为一个 All in One 用户，又不想为此多开一个软件，故自制了本 workflow。
- 本 workflow 组合了多种触发方式，以实现近似于独立软件的使用方式。
- 后续将考虑进行段落优化；同时组合更多特殊接口，如公式识别，识别翻译等，尽情期待。

## TODO

- [ ] 接入更多 API
  - [x] Google
  - [x] 腾讯优图
  - [ ] 有道翻译
  - [x] 彩云小译
- [x] 多文件识别
- [x] 表格识别
- [x] 二维码识别
- [ ] 段落优化
- [ ] 截图翻译
- [x] 文本翻译

## 致谢

1. 离线识别方案：[breezedeus/cnocr](https://github.com/breezedeus/cnocr)
2. 离线二维码识别方案：[dlenski/python-zxing](https://github.com/dlenski/python-zxing)
3. 系统截屏的方案：[ginfuru/alfred-screen-capture](https://github.com/ginfuru/alfred-screen-capture)
4. Workflow 的设计方案：[oott123/alfred-clipboard-ocr](https://github.com/oott123/alfred-clipboard-ocr)
5. 感谢下列用户对本项目的贡献：[Elvis Cai](https://github.com/elviscai)
