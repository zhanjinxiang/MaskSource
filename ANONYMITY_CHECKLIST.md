# 匿名提交检查清单

- [x] 压缩包中不包含`.git`目录和提交历史。
- [x] 文件名、README、源码注释中不含姓名、学校、学院、学号、邮箱和电话。
- [x] 不包含个人GitHub仓库地址、用户名或个人主页。
- [x] 不包含虚拟环境、日志、缓存、SQLite数据库和本机绝对路径。
- [x] 示例身份保持为`anonymous-*`，示例密钥仅用于演示。
- [x] 运行`python -m pytest`并确认全部通过。
- [x] 运行`python -m src.demo --output output/demo`并检查三个模块均为`verified: true`。
- [x] 从最终ZIP解压到新目录，再按README完成一次冷启动。
