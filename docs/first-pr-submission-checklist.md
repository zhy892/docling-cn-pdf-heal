# 第一次 Docling PR：提交内容与提交前检查

## 这一次只提交什么

**提交“默认关闭的文本层质量报告”，不提交 OCR 回退。**

建议目录和内容（以维护者在 Issue #2963 的回复为准）：

1. `docling/datamodel/pipeline_options.py`：新增 `TextLayerQualityCheckOptions`，含 `enabled=False`、`score_threshold`；接入 `PdfPipelineOptions` 和 `NativePdfPipelineOptions`。
2. 上游现有工具目录：新增纯 Python 的页文本评分函数和不可变报告对象；信号仅为显式字形/CID 标记、替换/私有/控制字符、空提取。
3. `NativePdfPipeline` 与标准 PDF 管线：在维护者指定的现有钩子收集报告；关闭时零执行、零输出变化。
4. 测试：默认关闭、正常中文、`/gid…`、`(cid:…)`、空提取、阈值边界、选项序列化。测试输入只用字符串或团队生成的小 PDF，不上传国标或 Issue 附件。
5. 文档：说明该功能只产生 `recommend_ocr`，并不执行 OCR 或修复字体映射。

## 明确不提交什么

- 不提交本项目的 Tesseract/Poppler 包装器、RAG 评测、真实 PDF、全页 OCR 开关或表格回写；
- 不引入新模型、大型依赖或外部服务；
- 不宣称解决 #2963/#3081/#3582，也不将 OCR 结果自动覆盖文本层；
- 不在没有维护者确认扩展元数据 API 前新增不稳定的公开 schema 字段。

## 本地提交前必过

当前上游 `CONTRIBUTING.md` 要求使用 `uv`，并建议运行 `prek`、Ruff、ty 和回归测试。提交前在自己的 fork 分支执行：

```bash
uv sync
uv run prek run --all-files
uv run pytest
```

若变更影响上游参考转换结果，再按其说明以 `DOCLING_GEN_TEST_DATA=1 uv run pytest` 生成并人工审查参考数据；第一次 PR 的目标是避免触碰参考结果。

## PR 标题与说明模板

标题：`feat(pdf): add opt-in page text-layer quality reports`

说明必须包含：

- 关联 `Fixes`/`Refs #2963`，但不写已修复；
- 默认关闭和无行为变化证据；
- 每种信号与测试覆盖；
- 不新增依赖、不运行 OCR、不修改 `DoclingDocument` 正文；
- 合成测试资料来源与许可；
- 已运行的精确命令及结果。

## 真正需要你操作时的顺序

1. 用 `zhy892` 登录 GitHub，fork `docling-project/docling`；
2. 在 #2963 发布本项目的英文设计留言，等待维护者对元数据位置与管线钩子的答复；
3. 收到答复后，我把最小 PR 补丁应用到你的 fork 分支、复跑上游检查；
4. 你在网页点击 “Create pull request”。提交前你只需核对署名和 PR 文案；不要上传真实 PDF 或任何密钥。
