# alfred-ocr

> 由于没有项目开发经验，肯定会有一些没能处理的异常，欢迎您的使用和反馈。觉得好用的请点个 star，谢谢～

## Demo

![Demo](./demo.gif)

## 版本

### 2.5 (2019-11-28 23:18)

- 优化速度：百度接口的 token 有效期为 2592000 s (30 d)，数据将被保存在`./baidu_api_token.json`并每 30 天更新一次，减少请求时间

<details>
  <summary>历史版本</summary>

### 2.4 (2019-11-28 10:49)

- 临时截图文件移动至`/tmp/ocr_screenshot.png`
- 不再使用`rm`删除临时文件

### 2.3 (2019-11-27 19:36)

- Python 路径由环境变量直接提供（需自行修改）
- api_key 由 Python 直接获取环境变量
  </details>

## 接口

### CNOCR

#### 说明

1. 项目地址: [CNOCR](https://github.com/breezedeus/cnocr)
2. 只支持 Python3
3. 一切安装方法请依据该项目 [README](https://github.com/breezedeus/cnocr/blob/master/README.md)。

### Baidu OCR

#### 说明

1. 官方地址: [Baidu OCR](https://ai.baidu.com/tech/ocr)
2. 考虑到不能准确判别中英文符号，所有的英文逗号将被全部替换为中文逗号；但由于句点和括号可能存在其他用途，不做处理。
3. 需自行申请 api_key 和 secret_key。

## 依赖

### CNOCR

```python
pip install cnocr
```

### 其他

```python
pip install requests
```

## TODO

- [ ] 完善代码和文档
- [ ] 有(bing)时(mei)间(you)尝试接入更多 OCR 平台
- [ ] 多文件识别
- [ ] 截图翻译

## 致谢

1. [breezedeus/cnocr](https://github.com/breezedeus/cnocr)
2. 调用系统截屏的方案源于：[ginfuru/alfred-screen-capture](https://github.com/ginfuru/alfred-screen-capture)
3. Alfred Workflow 的设计方案来源于：[oott123/alfred-clipboard-ocr](https://github.com/oott123/alfred-clipboard-ocr)
