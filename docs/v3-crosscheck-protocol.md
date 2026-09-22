# V3 形似汉字乱码交叉审计协议

## 目的与边界

V3 是独立于 V2 的小型合成**转写**基准，验证 OCR 与文本层的第二测量是否能发现
“表面像中文、实为字形错位”的文本。它不替代 V2 的 PDF 路由评测，不改变 V2 的
文件、标签、阈值或既有结果。

第二阶段的输出只有 `manual_review` 建议：OCR 不被当作真值，系统不会自动以 OCR
文本覆盖文本层。

## 故障类型

- ASCII/标准编号映射为形似汉字，如 `GB/T` → `犌犅／犜`；
- 字母数字标识映射为形似汉字或中文数词，如 `AIC-2026-042` 与 `API v2.0`；
- 正常中文和版式差异对照页。

所有句子均为团队自制，不含真实国标、教材、论文或用户 PDF。

## 固定规则

1. 将文本层与独立 OCR 转写先作 NFKC 与空白无关规范化；
2. 全页一致率低于固定阈值 `0.65`，建议人工复核；
3. 即使全页一致率较高，若 OCR 含有而文本层缺失的字母数字技术标识符，也建议人工
   复核，原因为 `ocr_identifier_disagreement`；
4. 短文本保持 `insufficient_text`，不产生自动结论；
5. 标签只在建议生成后用于计算 Precision、Recall、F1，不参与逐页决策。

## 当前可复现结果与限制

V3 共有 8 页转写：开发 4 页、冻结测试 4 页，各含 2 页损坏样本。本次固定规则在
开发集和冻结测试集上均为 Precision=1、Recall=1、F1=1。该结果只适用于这 8 条
团队自制转写，不能声称对真实中文 PDF 或真实 OCR 噪声具有同等效果。

后续需收集经授权的本地真实样本匿名统计；真实 PDF、路径、截图内容和 OCR 原文
均不得进入公开仓库或主指标。

## 复现命令

```bash
python benchmark/generate_crosscheck_v3.py --output-dir benchmark/generated-crosscheck-v3
python benchmark/run_crosscheck_benchmark.py \
  --text-layer benchmark/generated-crosscheck-v3/text_layer.json \
  --ocr-transcript benchmark/generated-crosscheck-v3/ocr_transcript.json \
  --labels benchmark/generated-crosscheck-v3/labels.json \
  --output benchmark/generated-crosscheck-v3/results.json
```

输出将开发集与 `frozen_test` 分开保存；后者的 `manual_review_pages` 保留原始全局页号。
