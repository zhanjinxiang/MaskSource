# 开源组件与使用说明

本文件列出当前可运行参赛版**实际导入和执行**的第三方组件，避免把作品报告中的实验对象误写成当前轻量程序依赖。

| 组件 | 用途 | 当前代码位置 |
|---|---|---|
| Flask | 本地Web客户端与JSON API | `src/client/app.py` |
| NumPy | 确定性Logits模拟、数值计算与图像数组处理 | `src/content_watermark/codec.py`、`src/image_watermark/codec.py` |
| Pillow | PNG读取、生成和保存 | 模型触发图、DWT水印与演示资产 |
| PyWavelets | Haar DWT/IWT | `src/image_watermark/codec.py` |
| PyYAML | 配置读取扩展接口 | `config/` |
| pytest | 功能和端到端自动测试 | `tests/` |
| Python标准库 | SHA-256、MD5种子、HMAC、SQLite、JSON | `src/common.py`、`src/storage.py` |

## 作品报告中的研究对象

作品报告讨论或实验使用过CLIP、OpenCLIP、BLIP、LLaVA、Llama、ViT-GPT2、Caltech101、OxfordPets、Flowers102、Food101、FGVCAircraft、SUN397、DTD、EuroSAT和UCF101等模型或数据集。这些内容属于研究背景与既有实验记录，当前轻量参赛版不会自动下载，也不会宣称重新训练了它们。

## 算法来源说明

- DWT/IWT属于通用信号处理方法，通过PyWavelets调用。
- SHA-256、MD5、HMAC和PRNG使用Python标准库实现。
- 熵引导动态嵌入、2/4/8多列表编码、定向Logits偏置及双密钥组合方式依据本作品设计报告实现。
- 本仓库没有复制外部项目的模型训练源码或预训练权重。

第三方组件分别受其原始开源许可证约束；本项目自身许可证见`LICENSE`。
