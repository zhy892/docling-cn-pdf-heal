# 证据日志

| 日期 | 事件 | 证据位置 | 结论 |
|---|---|---|---|
| 2026-09-20 | 项目初始化 | 首次本地测试 | 待补充 |
| 2026-09-20 | 合成 CMap 故障注入 | `benchmark/generate_synthetic_pdf.py` | 正常 PDF 两页均保持文本层；损坏 PDF 两页均出现私有区字符并触发回退 |
| 2026-09-20 | Docling 无模型基线 | `pdf-heal ... --backend native-docling` | NativePdfPipeline 保留页码溯源，检测器在损坏 PDF 的两页均触发 OCR 回退 |
| 2026-09-20 | 冻结合成集 v1 三基线（3 次后热运行，当前代码重跑） | `benchmark/run_synthetic_benchmark.py` 输出 `/tmp/synthetic-v1-test-repeat3-v2code.json` | 8 页测试集：检测 TP=4、FP=0、FN=0（P/R/F1=1.0）；clean 0/4、错误 ToUnicode 2/2、扫描图像 2/2 页进入最终 OCR。Docling 原生层平均 CER=0.500000；全页 OCR=0.022222、选择性回退=0.011111。全页 OCR 中位 6.066127 秒，选择性回退中位总计 4.404810 秒、仅 OCR 4/8 页，空白守卫未跳过任何页。仅适用于该固定受控合成集，不能外推到真实文档。 |
| 2026-09-20 | 选择性 OCR CLI | `pdf-heal ... --recover` | 仅第 1 页触发 Tesseract `chi_sim`，第 2 页维持 Docling 文本层；命令行输出路由证据和恢复文本。 |
| 2026-09-20 | 真实公开样本本地审计：Docling #3081 附件 | 来源 `https://github.com/docling-project/docling/issues/3081`；本地临时文件，不入库 | 当前环境的 Docling NativePdfPipeline 完成 115 页解析，0 页触发本项目的规则。该附件在当前版本未复现 Issue 描述的可检测字形 ID 问题；不据此宣称上游问题已修复，也不报告 CER。 |
| 2026-09-20 | 非空白乱码 OCR 交叉校验单元 | `tests/test_crosscheck.py` | 先测试再实现：表面为汉字的错映射示例与 OCR 转写不一致时触发 `ocr_text_disagreement`；仅排版差异不触发；短文本明确返回 `insufficient_text`。这是接口级对抗测试，不是对真实文档的性能宣称。 |
| 2026-09-20 | OCR 转写审计 CLI 端到端验证 | `pdf-heal examples/crosscheck-pages.json --ocr-transcript examples/ocr-transcript.json` | 两页对抗示例：第 1 页规范化一致率 1.000000、不触发；第 2 页 0.555556、进入 `disagreement_pages=[2]`。命令只读取已有转写，不调用 OCR。该示例用于功能可核验性，不构成真实数据性能结果。 |
| 2026-09-20 | 交叉审计三态输出 | `tests/test_cli_audit.py` 与同一 CLI 示例 | 先写失败测试，再实现：文本层与 OCR 冲突时输出 `manual_review`，一致时输出 `keep_text_layer`；不会把 OCR 转写静默覆盖原文本。16 项测试、静态检查与格式检查通过。 |
| 2026-09-20 | 空白页误报控制 | `tests/test_page_ink.py`、`tests/test_recovery_blank_pages.py`、本地自生成 `/tmp/aic-blank-page.pdf` | 先写失败测试，再实现：二进制 PGM 解析不吞掉首像素；视觉空白页跳过 OCR；渲染失败保留 OCR 候选。真实 CLI 链路中自生成空白页得到 `ocr_pages=[]`、`skipped_blank_pages=[1]`、深色像素 0。该结果仅验证功能，不构成真实文档性能结论。 |
| 2026-09-20 | 冻结合成集 v2 三基线（3 次后热运行） | `benchmark/generate_dataset_v2.py` 与 `benchmark/run_synthetic_benchmark.py` 输出 `/tmp/synthetic-v2-test-repeat3.json` | 10 页测试集：TP=3、FP=0、FN=0；空白页 0/2、正常页 0/5、错误 ToUnicode 1/1、扫描图像 2/2 页进入最终 OCR。初始候选 5 页，其中 2 页视觉空白跳过，最终 OCR 3 页。Docling 平均 CER=0.300000；全页 OCR=0.006452；选择性回退=0.002419。全页 OCR 中位 7.114264 秒，选择性回退中位总计 3.608302 秒。仅适用于自制受控 v2，不外推真实文档。 |
| 2026-09-20 | 真实样本匿名审计记录 | `tests/test_audit_record.py` 与本地自生成 PDF CLI | 先写失败测试，再实现：`--audit-id` 输出稳定 SHA-256、页数和候选统计，不输出原始路径、文件名或 PDF 内容。端到端样例验证无路径/文件名字段。该机制仅保护报告最小化披露，不赋予任何样本再分发权。 |
