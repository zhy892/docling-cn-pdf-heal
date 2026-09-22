# 开源及第三方资源工作清单

本表是竞赛附件《开源及第三方资源使用清单》的代码侧依据，最终提交前需再次对照锁文件和官方许可页核验版本。

| 资源 | 用途 | 许可与处理方式 | 公开边界 |
|---|---|---|---|
| [Docling](https://github.com/docling-project/docling) | 原生 PDF 文本层基线与潜在上游贡献对象 | MIT；保留版权和许可声明 | 作为安装依赖，不复制上游源码 |
| [pypdf](https://github.com/py-pdf/pypdf) | 合成 PDF 故障注入与轻量文本层读取 | BSD-3-Clause；保留许可证信息 | 作为安装依赖，不复制源码 |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | 本地 OCR 回退命令 | Apache-2.0；由用户单独安装 | 不随仓库分发二进制 |
| [tessdata_fast chi_sim](https://github.com/tesseract-ocr/tessdata_fast) | 中文 OCR 语言数据 | Apache-2.0；本地测试使用 | 不随仓库分发模型文件 |
| [Noto Sans SC](https://github.com/google/fonts/tree/main/ofl/notosanssc) | 合成 PDF 的可嵌入中文字体 | SIL Open Font License 1.1；本地生成时下载 | 仓库不附带字体文件；提交前确认是否公开生成 PDF |
| [ReportLab](https://www.reportlab.com/) | 生成团队自制合成 PDF | BSD license；作为安装依赖 | 不复制源码，不分发其安装包 |
| Poppler `pdftoppm` | 将被选 PDF 页渲染为 OCR 图像 | 外部系统依赖，最终发布形态前再核验其分发许可证与 NOTICE | 不随仓库分发二进制 |

## 已排除资源

- **PyMuPDF**：AGPL/commercial 双许可，不作为本项目的默认依赖或上游 PR 依赖。

## 团队自主开发边界

团队自主编写：文本层质量评分、页面路由、合成 CMap 故障注入、OCR 编排、CER 与基准脚本、测试、文档和演示材料。第三方标准 PDF 只可本地测试，不进入仓库或发布包。
