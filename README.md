# Alfred - OCR and Translation

## 语言

简体中文 | [English][1]

## 下载地址

[国内直链][2] | [Github-Release][3]

## OCR Demo

![Demo_OCR][image-1]

## Translate Demo

![Demo_Trans][image-2]

## 版本

### 4.8

- 支持 Mathpix 公式识别（因学业原因，仅支持识别后输出 Latex 格式文本，更多支持选项待后期开发）;
- 由于可选识别方式过多，CNOCR 的触发方式修改为唯一触发词 `ooc (CNOCR)`。

### 近期更新

- 紧急修复批量文件识别报错的问题；
- 更改 CNOCR 的触发方式，现与其余 OCR 一致；
- 支持百度 OCR 自定义语种识别，详情请见：[https://github.com/Chandler-Lu/alfred-ocr#自定义语种](https://github.com/Chandler-Lu/alfred-ocr#自定义语种)

## 能力

- 离线 OCR (CNOCR)
- 通用 OCR (百度 | 腾讯优图 | Google)
- 二维码识别 (百度 | ZXing)
- 表格文字识别 (百度)
- 数学公式识别 (Mathpix)
- 多文件识别 (百度)
- 文本翻译 (彩云小译)

## 使用（必看！！）

1. 这**不是**一个开箱即用的产品！
2. 您至少要拥有 macOS Alfred 3 及以上版本并激活 Powerpack。
3. 您需要安装 Python 3 及相应的依赖模块，并将 Python 3 路径填写在`PYTHON_PATH`处。
4. 您需要申请并将对应接口的配置填入环境变量，部分接口附带我自己的 Key，但严禁滥用。
5. 具体配置方法请移步 [安装方式][4]。

<!-- ### 截图权限

第一次使用时，请先用 `oo` 触发 CNOCR（无论你是否安装/需要 CNOCR 模块），此时 Alfred 会向系统请求屏幕录制权限，授权后，方可正常通过 `ctrl+v` 触发截屏。 -->

## 依赖

### 通用 OCR

```bash
pip install requests
```

### CNOCR (离线 OCR)

```bash
pip install cnocr
```

### ZXing (离线二维码识别)

```bash
pip install zxing
```

## 接口

### [CNOCR][5]

#### 触发

- 截图至剪贴板后使用关键词 `ooc` 触发。

#### 说明

- 一切安装方法请依据该项目 [README][6]。

### [Baidu AI (百度)][7]

#### 触发

1. 通用 OCR：快捷键 ctrl+v 触发截图选框，或截图至剪贴板后使用关键词 `oob (baidu)` 触发；
2. 二维码识别：截图后使用关键词 `ooqb (qr baidu)` 触发；
3. 表格文字识别：截图后使用关键词 `ooe (excel)` 触发，识别后可直接复制至 Excel；
4. 多文件识别：finder 中选中需要识别的图片并使用关键词 `oof (file)` 触发。

![File_OCR][image-3]

#### 说明

1. 具备中英文识别，标点符号将被替换为对应语言下的符号；
2. 二维码识别支持同时识别多个；
3. 自带一个测试 Token，不保证可用性，需要稳定可自行申请；
4. 最大支持单个 4MB 的图片。

#### 自定义语种

> 目前仅通用 OCR 支持选择语言

语种选择逻辑：

1. ctrl+v 或关键词 `oob` 触发时，将选择环境变量中的 `baidu_language_type` 来定义语种。如果该值为空，则定义为默认值 `CHN_ENG`，即中英文混合识别；
2. 当使用 `oob` 调出选择菜单，并按住 command 触发时，将使用第二语言识别。

第一语言选择位置：

![First_Lang_Select][image-4]

第二语言选择位置：

![Second_Lang_Select][image-5]

<details>
  <summary>支持的全部语种及其语种代码如下所示：</summary>

```
- CHN_ENG：中英文混合
- ENG：英文
- JAP：日语
- KOR：韩语
- FRE：法语
- SPA：西班牙语
- POR：葡萄牙语
- GER：德语
- ITA：意大利语
- RUS：俄语
```

</details>

### [Tencent Youtu (腾讯优图)][8]

#### 触发

- 通用 OCR：截图至剪贴板后使用关键词 `oot (tencent)` 触发。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请；
2. 最大支持 1MB 的图片，过大图片会自动交由百度处理（当然百度最大也只支持 4MB）。

### [Google OCR][9]

#### 触发

- 通用 OCR：截图至剪贴板后使用关键词 `oog (google)` 触发。

#### 环境变量

| 变量名              | 字段说明                                         |
| ------------------- | ------------------------------------------------ |
| google_access_token | 授权密钥                                         |
| google_post_referer | HTTP 请求时的 Referer 参数，默认为空             |
| google_http_proxy   | HTTP 代理，默认为空，填写方式如 `127.0.0.1:1234` |

#### 说明

- Google OCR 为收费业务，需绑定信用卡，故本项目不带测试 Token，需要自行申请。

### [Mathpix](https://mathpix.com)

#### 触发

- 公式识别：截图至剪贴板后使用关键词 `oom (mathpix)` 触发。

#### 说明

- Mathpix 为收费业务，需绑定信用卡，故本项目不带测试 Token，需要自行[申请](https://accounts.mathpix.com/ocr-api)。

### [ZXing][10]

#### 触发

- 截图至剪贴板后使用关键词 `ooq` 触发。

#### 说明

1. 一切安装方法请依据该项目 [README][11];
2. 仅支持单个二维码识别。

### [彩云小译][12]

#### 触发

- 文本翻译：使用关键词 `tc (translate caiyun) + 需要翻译的内容` 来触发；输出结果可通过 `command + c` 复制。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请；
2. 支持中译英，及 X 译中(X 为彩云小译已经支持的语言类别)。

## TODO

- 段落优化
- 截图翻译

## 致谢

1. [breezedeus/cnocr][13]
2. [dlenski/python-zxing][14]
3. [ginfuru/alfred-screen-capture][15]
4. [oott123/alfred-clipboard-ocr][16]

感谢以下小伙伴帮助测试：

1. [Elvis Cai][17]
2. [LucasZhan](https://github.com/LucasZhan)

[1]: https://github.com/Chandler-Lu/alfred-ocr/blob/master/README-EN.md
[2]: https://img.yeslu.cn/github/Capture_then_OCR.zip
[3]: https://github.com/Chandler-Lu/alfred-ocr/releases
[4]: https://www.yeslu.cn/archives/7fe802d0.html
[5]: https://github.com/breezedeus/cnocr
[6]: https://github.com/breezedeus/cnocr/blob/master/README.md
[7]: https://ai.baidu.com/tech/ocr
[8]: https://ai.qq.com/product/ocr.shtml#common
[9]: https://cloud.google.com/vision/docs/ocr
[10]: https://github.com/dlenski/python-zxing
[11]: https://github.com/dlenski/python-zxing/blob/master/README.md
[12]: https://fanyi.caiyunapp.com/#/api
[13]: https://github.com/breezedeus/cnocr
[14]: https://github.com/dlenski/python-zxing
[15]: https://github.com/ginfuru/alfred-screen-capture
[16]: https://github.com/oott123/alfred-clipboard-ocr
[17]: https://github.com/elviscai
[image-1]: examples/demo_ocr_cn.gif
[image-2]: examples/demo_trans.gif
[image-3]: examples/file_ocr.png
[image-4]: examples/first_lang_select.png
[image-5]: examples/second_lang_select.png
