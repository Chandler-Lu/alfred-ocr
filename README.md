# alfred-ocr

> 由于没有项目开发经验，代码的鲁棒性不足，肯定会有一些没能处理的异常，欢迎您的使用和反馈～

## 版本号 (2019-11-27 14:09)

2.2

## Demo

![Demo](./demo.gif)

## 接口

1. CNOCR (只支持 Python3)
2. Baidu OCR (考虑到不能准确判别英文和中文逗号，所有的英文逗号将被全部替换为中文逗号；但由于句点和括号可能存在其他用途，不做处理)

## 依赖

### CNOCR

``` python
pip install cnocr
```

### 其他

``` python
pip install requests
```

## 说明

1. [CNOCR](https://github.com/breezedeus/cnocr) 项目的一切安装方法请依据该项目 [README](https://github.com/breezedeus/cnocr/blob/master/README.md)。
2. [Baidu-OCR](https://ai.baidu.com/tech/ocr) 需自行申请 api_key 和 secret_key
3. 请自行修改 Python 路径

## TODO
- [ ] 完善代码和文档
- [ ] 有(bing)时(mei)间(you)尝试接入更多 OCR 平台

## 致谢

1. [breezedeus/cnocr](https://github.com/breezedeus/cnocr)
2. 调用系统截屏的方案源于：[ginfuru/alfred-screen-capture](https://github.com/ginfuru/alfred-screen-capture)
3. Alfred Workflow 的设计方案来源于：[oott123/alfred-clipboard-ocr](https://github.com/oott123/alfred-clipboard-ocr)
