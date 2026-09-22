# Docling 中文 PDF 乱码自愈增强

一个面向中文 PDF 入库的可解释页级质量路由与可复现评测原型。它不声称首创 OCR 回退；公开 Issue 是问题来源，团队贡献是“何时保留、何时建议 OCR、何时必须人工复核”的证据化决策。

## 当前能力

- 检测 `/gid00020`、`/G27`、`(cid:123)`、`GLYPH<...>` 等显式异常；
- 检测替换字符、私有区字符和嵌入式控制字符；
- 识别“页面存在但提取结果仅为空白”的字体解码失败；
- 对空提取候选页先做低分辨率可见墨迹检查，跳过真正空白页的无意义 OCR；
- 生成逐页质量分、异常原因与 `ocr_fallback` / `keep_text_layer` 决策；
- 不修改正常页，因此可作为“全页强制 OCR”的轻量替代路由层。
- 对已有 OCR 转写执行交叉审计，识别表面仍像汉字的潜在错映射；
- 随代码提供自制故障注入与冻结评测协议，而非分发受版权保护 PDF。
- 阈值可仅用开发集进行可复现校准；冻结测试集不参与阈值选择。

## 快速开始

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
pdf-heal examples/pages.json --output report.json
# 或直接检查 PDF 文本层
pdf-heal input.pdf --output report.json
# 使用 Docling 的无模型原生 PDF 后端作为文本层基线
pdf-heal input.pdf --backend native-docling --output report.json
# 仅对检测到的坏页运行本地 Tesseract OCR
pdf-heal input.pdf --backend native-docling --recover \
  --ocr-lang chi_sim --tessdata-dir /path/to/tessdata --output recovered.json
# 对已生成的 OCR 转写做交叉审计；本命令不会执行 OCR
pdf-heal examples/crosscheck-pages.json --ocr-transcript examples/ocr-transcript.json \
  --output audit.json
# 对只在本地保存的真实 PDF 生成匿名审计元数据；不输出路径或文件名
pdf-heal local-real-sample.pdf --backend native-docling --audit-id REAL-001 \
  --output local-audit.json
```

JSON 输入格式：

```json
{"pages": ["第一页提取文本", "第二页提取文本"]}
```

## 运行测试

核心测试不依赖未声明的测试框架；安装项目依赖后可直接运行：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## 生成冻结合成评测

下列命令将“文本层导出—仅开发集校准—冻结测试”显式分离。运行
`native-docling` 基线时，应固定并记录当前 Docling 版本；`chi_sim` 和
Poppler 是本地系统依赖。

```bash
python benchmark/generate_dataset_v2.py --font /path/to/NotoSansSC-wght.ttf \
  --output-dir benchmark/generated-v2
python benchmark/extract_text_layer_pages.py benchmark/generated-v2/synthetic_v2_all.pdf \
  --backend native-docling --output benchmark/generated-v2/all-pages-native-docling.json
python benchmark/calibrate_quality_threshold.py \
  benchmark/generated-v2/all-pages-native-docling.json \
  benchmark/generated-v2/manifest.json --output benchmark/generated-v2/calibration.json
python benchmark/run_synthetic_benchmark.py benchmark/generated-v2/synthetic_v2_test.pdf \
  benchmark/generated-v2/test_truth.json --labels benchmark/generated-v2/test_labels.json \
  --tessdata-dir /path/to/tessdata --calibration benchmark/generated-v2/calibration.json \
  --output benchmark/generated-v2/frozen-test-results.json
```

`--font` 必须是 ReportLab 可嵌入的 TrueType 字体（`.ttf`）。已验证
Noto Sans SC 的 TrueType 版本可用；部分 CFF `.otf` 版本会被 ReportLab
拒绝，不能用于本基准生成。

`calibration.json` 只能由 `split=development` 页面生成；最后一条命令的
`frozen-test-results.json` 才可用于比赛中的冻结测试结论。

输出是可存档、可审查的逐页 JSON 报告。PDF 模式默认使用 `pypdf`，也可使用 Docling 的无模型 `NativePdfPipeline`，后者能在不下载版面模型的前提下提供页面溯源。启用 `--recover` 时，系统只渲染并调用 Tesseract 处理被路由且具有可见墨迹的页面；真正空白页会在 `skipped_blank_pages` 与 `ink_estimates` 中留痕。若低分辨率渲染失败，系统按失败开放原则仍保留 OCR 候选，避免静默漏检。

`--ocr-transcript` 是单独的审计模式：输入同页数的 JSON OCR 转写，输出页级一致率、`insufficient_text` 或 `ocr_text_disagreement` 证据。它不把 OCR 当作真值，也不在后台触发全页 OCR。

`--audit-id` 用于真实样本的本地证据留存。输出只包含团队指定的样本编号、SHA-256、后端、页数和 OCR 候选统计，不含本地文件路径、文件名或 PDF 内容。它不构成对样本版权或再分发权的授权。

## 项目边界

本仓库只公开团队自主开发的检测、路由、测试和评测代码；真实标准 PDF 仅用于本地评测，不纳入仓库。

Docling #2963、#3081、#3582 是本项目的问题来源和对比依据。团队不声称首创“乱码回退 OCR”，也不声称解决所有上游乱码问题；完整归因与自主贡献边界见 [创新边界](docs/innovation-boundary.md)。

提交比赛材料前，可用 `anonymity_scan.scan_text_for_terms` 对报告、PPT 文本和视频字幕导出进行禁用词预检。禁用词由团队在本地传入（学校名称、成员姓名、教师姓名、邮箱域名等），不会硬编码或上传到仓库；扫描结果给出行列位置，供人工二次核对。

OCR 回退需要本地安装 `pdftoppm`（Poppler）和 Tesseract；中文识别需要用户自行安装 `chi_sim` 语言数据。它们均不随本仓库分发。

## 如何具体合入 Docling

不是把本仓库整体塞进上游。首次 PR 只提交默认关闭的逐页质量报告：在 `PdfPipelineOptions` / `NativePdfPipelineOptions` 增加选项，在原生页解析或全功能页组装后调用无依赖评分器，并把 `recommend_ocr` 及理由作为转换结果元数据输出。它不运行 OCR、不改写文本、不改变默认转换结果。维护者确认逐页 OCR 的公共/内部钩子后，才另开 PR 实现局部 OCR 调度。完整的文件位置、数据流、测试与 PR 切分见[具体合入设计](docs/docling-integration-plan.md)。

## 许可证

MIT。上游 Docling 及其模型、OCR 引擎和测试数据的许可条件须单独核验。
