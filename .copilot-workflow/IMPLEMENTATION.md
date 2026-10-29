# v0.1 实现记录

## 交付

已从空仓库实现用户确认的 v0.1 文档和技能范围：

| 文件 | 内容 |
|---|---|
| `standard/plain-chinese-standard.md` | 42 条编号规则、理由、反例、正例、适用范围，三层规则、两种模式、计数方法和词典种子 |
| `skills/simple-chinese/SKILL.md` | 中文触发词、文档核心 12 条、回复 6 条、模式、检查流程和自查，共 2230 字符 |
| `skills/simple-chinese/references/rule-catalog.md` | 构建生成的完整规范副本，不依赖安装目录之外的文件 |
| `skills/simple-chinese/references/word-swaps.md` | 常用词、套话替换、技术名词例外、情态词保真 |
| `skills/simple-chinese/references/use-cases.md` | 报错、发布说明、事故报告、提交信息和危险操作边界 |
| `prompts/system-prompt.md` | 独立完整版与约 150 字短版 |
| `examples/before-after.md` | 8 组示意对比、可复制的手动试写任务、来源记录要求 |
| `README.md` | 本地与发布后安装、使用、示例、版本边界、验收现状、英文简介和致谢 |
| `LICENSE`、技能内 `LICENSE.txt` | MIT 许可 |
| `scripts/build.py`、`.gitignore` | 无依赖本地构建、规则与链接检查、技能 ZIP 与 SHA-256，忽略本地产物 |

## 对草案的必要澄清

- 第 3.2 条服从事实保真：不能把概率改成确定性、把建议改成强制要求。
- 第 1.7 条完整词典检查在 v0.3，v0.1 不把所有未收录普通词报错。
- 草案“31 条种子”是 10 个批准词与 21 个不批准词组，不是 31 个独立词条。
- 保留技术术语、原始错误、代码、安全警告和危险操作确认，不让格式与字数覆盖保真要求。
- 8 组示例明确标为项目编写的示意，不能冒充真实模型输出或已完成实测。
- 不配置 GitHub Actions；后续数字复算以本地执行为准。

## 构建与产物

`python3 scripts/build.py` 已完成：42 条规则、R1–R6、技能长度及本地资源链接检查通过。
生成 `dist/simple-chinese-v0.1.zip`，内含技能入口、3 份参考文件和 MIT 许可，共 5 个文件。
已核对归档目录及 SHA-256 文件；产物未包含工作流状态或仓库历史。
没有执行测试、模型评测、收费 API 请求或技能安装；没有提交、推送或修改 issue。

## 未完成的验收

DeepSeek 与 GPT 的真实手动试写由用户执行，本次没有执行。
issue #1 要求的真实、未经修改的模型输出示例及“输出明显变短变直”验收尚未满足。
当前只交付可用的文档、技能、示意案例和手动验收材料，不宣称 v0.1 已通过真实模型验收。
后续正式评审尚未进行，状态移交为 `ready-for-review`，不标记 `approved`。
