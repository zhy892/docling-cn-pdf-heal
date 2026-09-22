# V2 原生 Docling 冻结评测记录

## 结论边界

本记录是一次可复现的**合成数据**运行，不代表真实国标、教材或任意第三方
PDF 上的效果，也不代表上游 Docling 已采纳本项目。它用于验证：文本层导出、
开发集阈值校准、空白页防护、选择性 OCR 和冻结测试之间的证据链能够完整执行。

## 固定环境

- 项目依赖锁定文件：`uv.lock`；运行时 Docling：`2.129.0`。
- OCR：Tesseract `5.3.4`，语言包 `chi_sim`。
- 栅格化：Poppler `pdftoppm 26.05.0`。
- 生成字体：Noto Sans SC TrueType 字体（本地路径不写入报告或结果 JSON）。
- 计时协议：每个方法先预热一次，随后运行三次，报告中位数；三种方法的顺序轮换。

## 可复现命令

```bash
uv sync --locked
uv run python -m unittest discover -s tests -p 'test_*.py'
uv run python benchmark/generate_dataset_v2.py --font /path/to/NotoSansSC-wght.ttf --output-dir <run-dir>
uv run python benchmark/extract_text_layer_pages.py <run-dir>/synthetic_v2_all.pdf --backend native-docling --output <run-dir>/all-pages-native-docling.json
uv run python benchmark/calibrate_quality_threshold.py <run-dir>/all-pages-native-docling.json <run-dir>/manifest.json --output <run-dir>/calibration.json
uv run python benchmark/run_synthetic_benchmark.py <run-dir>/synthetic_v2_test.pdf <run-dir>/test_truth.json --labels <run-dir>/test_labels.json --tessdata-dir /path/to/tessdata --calibration <run-dir>/calibration.json --output <run-dir>/frozen-test-results.json
```

## 本次冻结测试结果

数据集按 V2 协议生成：24 页合成样本，开发集 1–8 页、冻结测试集 9–18 页、保留集
19–24 页。阈值只使用开发集校准；本次得到阈值 `1.0`，开发集候选数为 2，开发集
F1 为 `0.857143`，误报率为 `0.2`。

冻结测试集（10 页）结果如下：

| 方法 | 平均 CER | 中位耗时（秒） | OCR 页数 |
| --- | ---: | ---: | ---: |
| 原生 Docling 文本层 | 0.300000 | 1.247541 | 0 |
| 全页 Tesseract OCR | 0.006452 | 7.817119 | 10 |
| 选择性 OCR 回退 | 0.002419 | 3.861393 | 3 |

在同一冻结测试集上，实际 OCR 路由的检测 Precision、Recall 和 F1 均为 `1.0`：2 个
扫描页和 1 个损坏 ToUnicode 页被送入 OCR，2 个真空白页被可见墨迹守卫跳过，5 个
干净页未被 OCR。该结果只说明这组受控生成条件下的表现；比赛材料必须同时展示
开发集误报率，不能只展示冻结测试 F1。

## 产物完整性（本次运行）

| 文件 | SHA-256 |
| --- | --- |
| `synthetic_v2_all.pdf` | `bf2635010127a2fccdf1498fd2e6e53f4d14754d201eaf0f75a22d2d1c640930` |
| `synthetic_v2_test.pdf` | `8215e3943a7f18eb8ef1881a39d0df7f50cd70b07c3451f799ddd3e5da30040c` |
| `manifest.json` | `1fcf5cace1c5ce6e35beb32d57c0a1334047993513154cf9e075d5b50310050e` |
| `all-pages-native-docling.json` | `849c1429af0150c5bc0448a537a87a71879e3a049eb851162c2769c277510196` |
| `calibration.json` | `3f3255b8bf7c5feda464c58da63e29c1f110227ad8204f4b17758b12437294d5` |
| `frozen-test-results.json` | `486d6cd6f6abcd9c338512c5ab274fde777ef9e4a31dca8735fe9520c25d4cce` |

评审复跑时应先校验哈希，再读取结果；若依赖版本、系统 OCR 版本或字体版本变化，
应创建新的运行目录与记录，而不是覆盖此记录。
