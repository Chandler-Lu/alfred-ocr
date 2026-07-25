# Alfred - OCR and Translation

## 下载地址

[Github](https://github.com/Chandler-Lu/alfred-ocr/releases) | [Quicker (Windows)](https://getquicker.net/Sharedaction?code=f73ca43a-98c6-475d-a3cc-08d7c216a695)

## OCR Demo

![Demo_OCR][image-1]

## Translate Demo

![Demo_Trans][image-2]

## 版本

### 5.0.0

- **重构为分层结构**：`core`（基础设施）+ `providers`（各引擎）+ `utils`（纯工具），入口统一为 `src/main.py`；新增引擎只需新增一个 Provider 子类并在 `router.py` 注册；
- **段落识别重写**：由「行距方差二选一」改为多信号加权判定（行距、行尾留白、首行缩进、字号变化、行尾标点、分栏、列表项），阈值全部相对于实测版面度量，同一段落的上下行不再插入回车；
- **中英文空格与标点重写**：按字符上下文而非整行判断，URL、邮箱、`1,000.50`、`f(x)`、`v1.2.3` 不再被破坏；跨行的中英文边界也能正确加空格；英文换行不再被粘连（`canhandle` → `can handle`），英文连字符断行自动还原；
- **健壮性**：所有网络请求增加超时、重试与统一代理；缺少某个密钥不再导致整个脚本崩溃；异常不会以 traceback 形式进入剪贴板；百度 Token 失效可自动刷新；
- 修复腾讯接口在网络异常时的 `NameError`；
- 新增单元测试与 `config/*.yaml` 配置支持。

### 4.9.6

- 使用 ZXing-C++ 进行二维码识别。

### 4.9.5

- 同步 macOS Alfred 版本；
- 优化代码；
- 修复百度表格识别。

### 4.9.2

- 支持 CNOCR 基于 FastAPI 的 HTTP  [服务模式](https://github.com/breezedeus/cnocr#http%E6%9C%8D%E5%8A%A1)，您可以使用[此方法](https://github.com/Chandler-Lu/alfred-ocr/wiki/Q&A#启用-cnocr-的-fastapi-服务模式-windows)注册 Windows 服务。

### 近期更新

- 百度 OCR 更换接口参数，已修复；
- 支持 Mathpix 公式识别；
- 删除腾讯优图接口，新增腾讯云文字识别接口（正式版）;
- 由于可选识别方式过多，CNOCR 的触发方式修改为唯一触发词 `ooc (CNOCR)`。

## 能力

- 离线 OCR (CNOCR)
- 通用 OCR (百度 | 腾讯 | Google)
- 二维码识别 (百度 | ZXing)
- 表格文字识别 (百度)
- 数学公式识别 (百度 | Mathpix)
- 多文件识别 (百度)
- 文本翻译 (彩云小译)

## 使用（必看！！）

1. 这**不是**一个开箱即用的产品！
2. 您至少要拥有 macOS Alfred 3 及以上版本并激活 Powerpack。
3. 您需要安装 Python 3 及相应的依赖模块，并将 Python 3 路径填写在`PYTHON_PATH`处。
4. 您需要申请并将对应接口的配置填入环境变量，部分接口附带我自己的 Key，但严禁滥用。
5. 具体配置方法请移步 [安装方式][4]。

### 命令行

统一入口为 `src/main.py`，服务可用数字（与旧版一致）、名称或 Alfred 关键词指定：

```bash
python src/main.py 1 /tmp/shot.png          # 数字选择器，兼容旧版 Action
python src/main.py baidu /tmp/shot.png      # 名称
python src/main.py oob -                    # 关键词，'-' 表示读取剪贴板图片
python src/main.py baidu https://host/a.png # 远程图片
python src/main.py translate "你好"          # 翻译
python src/main.py                          # 查看全部服务
```

可选参数：`--json`（输出 Alfred Script Filter JSON）、`--copy`（同时写入剪贴板）、`--debug`（把段落判定过程打到 stderr）。

> 旧入口 `src/ocr.py` 与 `src/translate.py` 仍然可用，它们会转发到 `main.py`，已安装的 Workflow 无需改动。

## 项目结构

```
src/
├── main.py            # 唯一入口
├── router.py          # ServiceRouter：数字/名称/关键词 → Provider
├── core/              # 公共基础设施
│   ├── base_provider.py   # BaseProvider 抽象基类 + OcrResult
│   ├── config.py          # 配置（默认值 + 配置文件 + 环境变量）
│   ├── auth_manager.py    # Token 获取、缓存、自动刷新
│   ├── http_client.py     # 超时、重试、代理、异常归一
│   ├── image_loader.py    # 文件 / URL / 剪贴板
│   ├── formatter.py       # 标点、中英文空格、结果渲染
│   ├── layout.py          # 行盒子 → 段落
│   ├── output.py          # stdout / Alfred JSON / 剪贴板 / 通知
│   └── exceptions.py      # 异常体系
├── providers/         # 各引擎实现（baidu / tencent / google / cnocr / mathpix / zxing / caiyun）
└── utils/             # 标点映射表、剪贴板封装
```

新增一个引擎：继承 `BaseProvider`，实现 `recognize()`，然后在 `router.py` 的 `PROVIDER_CLASSES` 中登记。

## 配置

优先级：环境变量 > `config/user.yaml` > `~/.config/alfred-ocr/config.yaml` > `config/default.yaml` > 内置默认值。
所有可调项及其说明见 [`config/default.yaml`](config/default.yaml)，每一项都能用同名环境变量覆盖（Alfred Workflow 变量即以此方式生效）。

密钥请放在环境变量或 `config/credentials.json`（已被 git 忽略），不要写进配置文件：

```json
{
  "baidu_api_key": "...",
  "baidu_secret_key": "..."
}
```

常用调节项：

| 配置项 | 默认值 | 说明 |
| ------ | ------ | ---- |
| `http_proxy` | `127.0.0.1:7890` | **全局代理**，对所有引擎生效；填 `""` 则直连 |
| `http_timeout` | `20.0` | 单次请求超时（秒） |
| `http_retries` | `2` | 网络抖动与 5xx 的重试次数 |
| `paragraph_enabled` | `true` | 关闭后每行单独成段 |
| `paragraph_gap_ratio` | `1.45` | 行距超过常规行距的多少倍算新段落 |
| `paragraph_short_line_chars` | `3.0` | 行尾留白多少个字算「这一行结束了」 |
| `paragraph_indent_chars` | `1.2` | 首行缩进多少个字算新段落 |
| `text_add_cjk_latin_space` | `true` | 中英文之间加空格 |
| `text_normalize_punctuation` | `true` | 标点按上下文转全角/半角 |
| `debug` | `false` | 输出段落判定依据到 stderr |

### 关于代理

`http_proxy` 是全局设置，由 `core/http_client.py` 统一注入，**所有引擎（含图片 URL 下载）都会走它**，不需要每个 provider 各自处理。

关闭代理有一处需要注意：**空的环境变量会被当作「未设置」**，因为 Alfred 会把 Workflow 里所有变量都导出，没填的那些不应该覆盖默认值。所以要直连，请在配置文件里写空值：

```yaml
# config/user.yaml
http_proxy: ""
```

## 开发

```bash
pip install -r requirements.txt
pip install pytest
python -m pytest tests -q
```

## 依赖

### 通用 OCR

```bash
pip install requests
```

### CNOCR (离线 OCR)

```bash
pip install cnocr[ort-cpu]
pip install cnocr[serve] # 针对 FastAPI 服务模式
```

### ZXing (离线二维码识别)

```bash
pip install zxing-cpp
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

1. 具备中英文识别；标点符号按上下文替换为对应语言下的符号，中英文之间自动补空格，URL、小数、`f(x)` 等不会被误伤；
2. 自动合并段落：属于同一段的上下行直接拼接，不插入回车（判定依据与阈值见「配置」一节）；
3. 二维码识别支持同时识别多个；
4. 自带一个测试 Token，不保证可用性，需要稳定可自行申请；
5. 最大支持单个 4MB 的图片。

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

### [Tencent (腾讯)][8]

#### 触发

- 通用 OCR：截图至剪贴板后使用关键词 `oot (tencent)` 触发。

#### 说明

1. 自带一个测试 Token，不保证可用性，需要稳定可自行申请；
2. 最大支持 3MB 的图片。

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

2. 支持中译英，及 X 译中(X 为彩云小译已经支持的语言类别)。

## TODO

- 截图翻译

### 项目

1. [breezedeus/cnocr][13]
2. [dlenski/python-zxing][14]
3. [ginfuru/alfred-screen-capture][15]
4. [oott123/alfred-clipboard-ocr][16]

### 用户

感谢以下小伙伴帮助测试：

1. [Elvis Cai][17]
2. [LucasZhan](https://github.com/LucasZhan)

[4]: https://www.yeslu.cn/archives/7fe802d0.html
[5]: https://github.com/breezedeus/cnocr
[6]: https://github.com/breezedeus/cnocr/blob/master/README.md
[7]: https://ai.baidu.com/tech/ocr
[8]: https://console.cloud.tencent.com/ocr/overview
[9]: https://cloud.google.com/vision/docs/ocr
[10]: https://github.com/dlenski/python-zxing
[11]: https://github.com/dlenski/python-zxing/blob/master/README.md
[12]: https://fanyi.caiyunapp.com/#/api
[13]: https://github.com/breezedeus/cnocr
[14]: https://github.com/dlenski/python-zxing
[15]: https://github.com/ginfuru/alfred-screen-capture
[16]: https://github.com/oott123/alfred-clipboard-ocr
[17]: https://github.com/elviscai
[image-1]: img/demo_ocr_cn.gif
[image-2]: img/demo_trans.gif
[image-3]: img/file_ocr.png
[image-4]: img/first_lang_selection.png
[image-5]: img/second_lang_selection.png
[image-6]: img/jetbrains_logo.png
[image-7]: img/ocr_abuse.png
