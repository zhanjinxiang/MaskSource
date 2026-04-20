# MaskSource

面向视觉语言模型的“双盾双溯源”版权保护系统 - 可运行参赛演示版。

本仓库依据作品设计报告重建了一套能够在普通电脑上独立安装、启动、操作和测试的参考实现，覆盖以下闭环：

1. 模型盾：将签名所有权记录写入可移植模型工件，并由提示密钥与图像密钥共同触发所有权验证。
2. 内容盾：SHA-256版权载荷、秘密图像派生密钥、熵引导2/4/8列表编码、Logits定向偏置和逐词元提取。
3. 图像水印：基于DWT高频子带的可嵌入、可提取参考后端。
4. 证据链：本地SQLite记录验证结果并通过API查询。
5. 客户端：支持一键演示、文本水印嵌入/验证和证据导出的本地Web界面。

## 一分钟启动

### Windows 11

双击 `start_windows.bat`，脚本将自动创建虚拟环境、安装依赖并启动系统；浏览器访问：

```text
http://127.0.0.1:8080
```

也可以在PowerShell中手动执行：

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.client.app
```

若PowerShell阻止激活脚本，可直接运行：

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m src.client.app
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.client.app
```

## 运行端到端演示

无需准备模型权重或数据集：

```bash
python -m src.demo --output output/demo
```

程序会自动生成匿名演示资产，并依次完成：

- 双密钥模型注册和所有权验证；
- 96位身份载荷生成、文本水印嵌入与提取；
- 48位DWT图像水印嵌入与提取；
- PSNR与SSIM质量计算；
- `output/demo/demo_report.json`证据报告输出。

## 运行测试

```bash
python -m pytest
```

14项测试不是占位断言，实际覆盖正确触发、单触发拒绝、内嵌记录与外部清单一致性、模型篡改拒绝、配置加载、错误身份拒绝、文本逐比特恢复与局部编辑重同步、图像水印恢复与JPEG压缩、质量指标和Web API完整流程。

## 命令行使用

### 1. 注册模型版权

```bash
python -m src.model_watermark.train \
  --model output/demo/demo_vlm.bin \
  --trigger-image output/demo/trigger.png \
  --prompt "verify authorized model ownership" \
  --owner "anonymous-owner-001" \
  --secret "local-demo-key" \
  --output output/demo/model_manifest.json \
  --protected-model output/demo/protected_demo_vlm.bin
```

### 2. 验证模型版权

```bash
python -m src.model_watermark.verify \
  --model output/demo/protected_demo_vlm.bin \
  --manifest output/demo/model_manifest.json \
  --trigger-image output/demo/trigger.png \
  --prompt "verify authorized model ownership" \
  --secret "local-demo-key"
```

只有提示密钥与图像密钥同时匹配时，`dual_trigger`和`verified`才会为`true`。

### 3. 嵌入文本水印

```bash
python -m src.content_watermark.inject \
  --identity "anonymous-user" \
  --timestamp "session-01" \
  --secret-image output/demo/secret.png
```

### 4. 验证文本水印

将上一步输出中的`text`传入：

```bash
python -m src.content_watermark.verify \
  --text "watermarked token sequence" \
  --identity "anonymous-user" \
  --timestamp "session-01" \
  --secret-image output/demo/secret.png
```

## 算法与作品报告的对应关系

| 作品报告模块 | 本仓库实现 |
|---|---|
| 身份信息序列生成 | `src/content_watermark/payload.py` |
| 熵计算与阈值选取 | `entropy_from_logits()`、`bits_for_entropy()` |
| 2/4/8多列表编码 | `src/content_watermark/codec.py` |
| Logits定向偏置 | `embed_payload()`中的目标列表偏置 |
| 逐词元提取与BER验证 | `extract_bits()`、`verify_payload()` |
| 提示-图像双密钥验证 | `src/model_watermark/core.py` |
| DWT高频水印 | `src/image_watermark/codec.py` |
| 用户操作与证据管理 | `src/client/app.py`、`src/storage.py` |

## Web API

| 方法 | 地址 | 作用 |
|---|---|---|
| GET | `/api/health` | 服务健康检查 |
| POST | `/api/demo/run` | 运行完整演示 |
| POST | `/api/content/embed` | 上传秘密图像并生成水印文本 |
| POST | `/api/content/verify` | 提取并验证文本水印 |
| GET | `/api/evidence` | 查询本地证据记录 |

## 项目结构

```text
MaskSource/
├── config/                         参数配置
├── scripts/                        演示辅助脚本
├── src/
│   ├── client/                     Flask客户端和API
│   ├── content_watermark/          熵引导多列表文本水印
│   ├── image_watermark/            DWT图像水印
│   ├── model_watermark/            双密钥模型验证
│   ├── common.py                   哈希、比特与JSON工具
│   ├── demo.py                     端到端演示
│   └── storage.py                  SQLite证据存储
├── tests/                          功能与端到端测试
├── requirements.txt
├── pyproject.toml
└── start_windows.bat
```

## 实现边界与结果说明

本参赛版的目标是让评委能够复核软件流程与核心算法接口，因此使用本地确定性采样器替代需要大量显存和数据集的VLM生成过程。模型侧会把签名所有权记录写入受保护模型工件，同时导出可独立审计的清单；验证时校验模型主体摘要、内外记录一致性以及提示-图像双密钥。代码真实执行配置加载、熵计算、多列表划分、定向偏置、分帧同步解码、冗余DWT嵌入和证据记录。

文本编码采用短帧同步标记，把插入、删除或替换造成的错位限制在单帧；图像后端在DWT低频系数中采用奇偶量化和多数投票，在演示测试中覆盖JPEG质量60压缩。上述测试结果只代表仓库内给定用例，不等同于完整攻击基准。

作品设计报告中的大模型训练指标属于既有实验记录，不是本轻量版本现场重新训练所得。程序生成的`demo_report.json`只报告本次运行的实测结果，二者不得混写。

## 匿名与安全

- 演示身份默认使用`anonymous-owner-001`，不包含姓名、学校或联系方式。
- 不提交`.git`、虚拟环境、缓存、日志、数据库或本机绝对路径。
- 示例密钥只用于本地演示，生产部署必须从环境变量或密钥服务读取。
- 系统仅监听`127.0.0.1`，默认不对公网开放。
- Web端为单机评审演示，不提供生产级账户、角色和公网部署能力。

开源组件及其用途见`OPEN_SOURCE.md`。
