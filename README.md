# alfred-ocr

> 觉得好用的请点个 star，谢谢～ 由于没有项目开发经验，肯定会有一些没能处理的异常，欢迎您的使用和反馈。

## Demo

![Demo](./demo.gif)

## 版本

### 3.0 (2019-12-01 21:45)

- 支持彩云小译接口进行文本翻译

<details>
  <summary>历史版本</summary>

### 2.9 (2019-12-01 10:30)

- 支持百度接口识别多个二维码

### 2.7 (2019-11-30 11:06)

- 支持检查并下载更新

### 2.6 (2019-11-29 21:59)

- 支持腾讯优图
- 重写部分代码，为批量识图作准备

### 2.5 (2019-11-28 23:18)

- 优化速度: 百度接口的 token 有效期为 2592000 s (30 d)，数据将被保存在`./baidu_api_token.json`并每 30 天更新一次，减少请求时间

### 2.4 (2019-11-28 10:49)

- 临时截图文件移动至`/tmp/ocr_screenshot.png`
- 不再使用`rm`删除临时文件

### 2.3 (2019-11-27 19:36)

- Python 路径由环境变量直接提供（需自行修改）
- api_key 由 Python 直接获取环境变量
  </details>

## 能力

- 离线 OCR (CNOCR)
- 通用 OCR (百度，腾讯优图)
- 二维码识别 (百度)
- 文本翻译 (彩云小译)

## 接口

### [CNOCR](https://github.com/breezedeus/cnocr)

#### 触发

1. 通用 OCR: 使用关键词 oo 触发截图选框。

#### 说明

1. 一切安装方法请依据该项目 [README](https://github.com/breezedeus/cnocr/blob/master/README.md)。

### [Baidu AI (百度)](https://ai.baidu.com/tech/ocr)

#### 触发

1. 通用 OCR: 快捷键 ctrl+v 触发截图选框，或截图后使用关键词 oob (baidu) 触发。
2. 二维码识别: 截图后使用关键词 ooq (qr code) 触发。

#### 说明

1. 考虑到不能准确判别中英文符号，所有的英文逗号将被全部替换为中文逗号；但由于句点和括号可能存在其他用途，不做处理。
2. 需自行申请 api_key 和 secret_key。

### [Tencent Youtu (腾讯优图)](https://ai.qq.com/product/ocr.shtml#common)

> 已知问题: 腾讯优图仅支持 1MB 以内的图片，超大图片会自动交由百度处理（当然百度最大也只支持 4MB）。

#### 触发

1. 通用 OCR: 截图后使用关键词 oot (tencent) 触发。

#### 说明

1. 同百度处理方式。
2. 需自行申请 appid 和 appkey。

### [ColorfulClouds (彩云小译)](https://fanyi.caiyunapp.com/#/api)

#### 触发

1. 文本翻译: 使用关键词 tc (translate caiyun) + 需要翻译的内容来触发。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请。
2. 目标语言目前只支持中文。

## 依赖

### CNOCR

```python
pip install cnocr
```

### 其他

```python
pip install requests
```

## 说明

- 虽然已经有很多大佬做过类似的 workflow，但是依然存在一些痛点没能解决；而作为一个 All in One 用户，又不想为此多开一个软件，故自制了本 workflow。
- 本 workflow 组合了多种触发方式，以实现近似于独立软件的使用方式。
- 后续将考虑进行段落优化；同时组合更多特殊接口，如公式识别，识别翻译等，尽情期待。

## TODO

- [ ] 接入更多 API
  - [ ] Google
  - [x] 彩云小译
  - [x] 腾讯优图
- [ ] 多文件识别
- [ ] 截图翻译
- [x] 二维码识别
- [x] 文本翻译

## 致谢

1. [breezedeus/cnocr](https://github.com/breezedeus/cnocr)
2. 调用系统截屏的方案源于: [ginfuru/alfred-screen-capture](https://github.com/ginfuru/alfred-screen-capture)
3. Alfred Workflow 的设计方案来源于: [oott123/alfred-clipboard-ocr](https://github.com/oott123/alfred-clipboard-ocr)
