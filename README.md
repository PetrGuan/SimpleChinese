# SimpleChinese

用简明中文写技术文档和对话回复。默认说白话；需要更明确的句长约束时，对技术文档启用严格模式。
项目包含一份中文原创规范和一个 Agent Skill，不需要运行服务。

v0.1.2 候选保留 42 条编号规则和 6 条回复规则，针对评审发现的待办分散和冗余操作解释作了修订。
交接动作集中呈现，必要标题不按句数硬删；熟练读者不重复解释已知用途，新手需要的限制和解释仍保留。
普通任务不预读全部参考资料；完整独立提示从技能核心生成，避免入口规则不一致。
最近一轮生成实验及 Grok 盲评属于 v0.1.1，不能沿用为本次修订成绩。v0.1.2 尚未实测，双生成模型及保留集验收尚未完成，不宣称已证明稳定提升。

## 安装

在支持技能的工具中运行：

```bash
npx skills add PetrGuan/SimpleChinese
```

选择 `simple-chinese` 和要安装到的工具。`skills` CLI 的 Node.js 要求与安装路径见其[官方说明](https://github.com/vercel-labs/skills)。
如需安装本地工作区版本，在仓库根目录运行：

```bash
npx skills add . --skill simple-chinese
```

也可以把整个 `skills/simple-chinese/` 目录复制到工具支持的技能目录；不要只复制 `SKILL.md`，检查模式需要随附的 `references/`。
不支持技能的工具可以复制 [系统提示](prompts/system-prompt.md) 中的完整版或短版，无需安装 Python 或 Node.js。

## 使用

```text
说人话，解释这条报错。保留错误原文，不要猜测原因。
把这段技术文档改成通俗的。
严格模式，改写这些操作步骤，保留命令和执行顺序。
按简明中文规范检查这段文档，列出原句、条号和改法。
```

| 模式 | 文档 | 对话回复 |
|---|---|---|
| 白话，默认 | 句子尽量短，术语一致，条件在前 | 首句给答案，解释写段落，短回复不用装饰格式 |
| 严格 | 步骤最多 30 字，说明最多 40 字，定语最多 12 字，名词前最多两个“的” | 仍用回复规则，不套用文档字数上限 |

严格模式的计数方法见 [规范全文](standard/plain-chinese-standard.md)。列表项同样计数，不能用列表绕过上限。
v0.1 只有词语种子分组，没有完整受控词典。第 1.7 条的全面检查及词典量词检查留待 v0.3，不能宣称已完全合规。
错误原文、代码、数字、不确定性、安全警告和危险操作确认优先保留，不能为缩短文字而改动事实或删掉风险。

v0.1 只支持简体中文技术文档和对话回复，不提供营销模式、繁体版本或插件。
反套话基础规则可以用于其他文字，但不是 AI 检测器，也不能证明作者身份。

## 改写示例

改写前（项目编写的示意，不是实测输出）：

> 我们很高兴地宣布，1.2.0 重磅发布！此次升级不仅是一次修复，更是对使用体验的全面赋能。我们修复了重复导出的问题，旧配置依然可用，并且无需迁移数据。总而言之，这次更新意义重大！

改写后：

> 1.2.0 修复了重复导出的问题。旧配置仍然可用，无需迁移数据。

[全部 8 组示例](examples/before-after.md) 包含安装步骤、功能说明、报错回复、发布说明、事故报告、提交信息、短回复和危险操作确认。
文件末尾提供 DeepSeek/GPT 手动试写方法，明确区分示意、参考改写和未经修改的真实输出。

## 文件

| 文件 | 用途 |
|---|---|
| [规范全文](standard/plain-chinese-standard.md) | 唯一规则编辑源：42 条规则、理由、反例、正例、范围和计数方法 |
| [SKILL.md](skills/simple-chinese/SKILL.md) | 技能入口，控制在 3000 字符以内 |
| [规则目录](skills/simple-chinese/references/rule-catalog.md) | 构建生成的完整规范副本，安装后可独立引用 |
| [词语替换](skills/simple-chinese/references/word-swaps.md) | 改写方向、技术术语例外和保真边界 |
| [使用场景](skills/simple-chinese/references/use-cases.md) | 报错、发布说明、事故报告和提交信息 |
| [系统提示](prompts/system-prompt.md) | 独立完整版和约 150 字短版 |
| [示例与手动验收](examples/before-after.md) | 8 组对比、试写输入和来源要求 |

## 本地构建

构建只需要 Python 3.9 或更新版本，使用标准库，无需安装依赖。
修改规范后运行下面的命令，再一并保留生成的规则目录和技能许可文件。
不要直接编辑生成的 `references/rule-catalog.md` 或 `skills/simple-chinese/LICENSE.txt`。
`prompts/system-prompt.md` 的完整版区域也由构建生成；修改对应的 SKILL.md 核心规则。

```bash
python3 scripts/build.py
```

构建检查条号、技能元数据与长度、文档相对链接，并把完整规则和 MIT 许可打进独立技能包。
产物为 `dist/simple-chinese-v0.1.2.zip` 和对应 `.zip.sha256` 摘要文件，归档根目录是 `simple-chinese/`。
解压后的目录可以作为整个技能目录安装；压缩包不包含工作流文件、仓库历史或本地配置。
构建不执行测试、不调用模型、不访问网络。仓库不配置 GitHub Actions。

## 验收与后续版本

评测方法依据 [SimpleEnglish 源码核查](evals/simpleenglish-research.md) 改进，操作与限制见 [评测协议](evals/README.md)。
已完成实验见 [公开结果摘要](evals/RESULTS.md)。原始实验记录因包含运行元数据留在本地，不随仓库发布；摘要不等同于可独立复核的完整证据。
现有示意案例与旧试写留作历史，不当新版证据。新矩阵比较无提示、v0.1、新版和固定短提示，按文体分组并重复采样。
16 个新场景分为 3 个开发任务和 13 个保留任务；原文保护、格式统计、语义和自然度分别判断。
原始 CLI 输出、提示、模型设置和哈希用于离线复算。没有盲评前不宣布胜率，没有保留集结果前不宣布普遍效果。
DeepSeek 与原定双模型验收仍未完成。
下一轮需验证待办是否集中且完整、熟练读者是否少读无用解释，以及新手是否仍得到必要限制；不靠减少标题或字数判胜，不改历史场景、原始输出或裁判评分。
英文缩写 PCS 暂定；用于校准字数上限的真实中文技术文档来源尚待确定。

| 版本 | 后续范围 |
|---|---|
| v0.2 | 在现有运行器、16 场景与复算基础上完成保留集及双模型评测、真实语料校准 |
| v0.3 | 200 条受控词典、严格词典检测、Claude Code/Codex 插件、会话钩子和输出风格 |
| v0.4 | App 介绍和销售邮件等营销模式 |
| 以后 | 社区词条流程、繁体和其他文体 |

原草案的双模型预算约 10 美元；增加旧版对照或裁判会改变调用量，必须重新确认预算，不能沿用旧的 192 次估计。
当前运行器使用 Copilot 账户额度，不把额度数换算成美元。只有显式运行 `run` 才发起模型请求。
未来报告先展示读者能看到的缺陷，不把检测脚本得分当作可读性证明，也不预先声称完整技能胜过短提示。

## 许可与致谢

代码和规范使用 [MIT 许可](LICENSE)。规范由中文原创，不复制或翻译 ASD-STE100 的规则原文和词典。
章节组织参考 ASD-STE100 Issue 9 的框架；本项目与 ASD、STEMG 没有关系，也没有得到它们认可。
ASD-STE100 是 ASD 的注册商标。本项目不声称符合任何官方标准或取得认证。

项目结构与评测思路参考 [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)（MIT）；本版本没有复用其脚本代码。
排版参考 [中文文案排版指北](https://github.com/sparanoid/chinese-copywriting-guidelines) 和 [中文技术文档的写作规范](https://github.com/ruanyf/document-style-guide)。
中文标点、数字分别参考 GB/T 15834-2011、GB/T 15835-2011；本项目不重印标准正文。
设计依据为 [issue #1](https://github.com/PetrGuan/SimpleChinese/issues/1)。

## English

SimpleChinese is an Agent Skill for clear Simplified Chinese technical writing and conversational replies.
It includes an original 42-rule Plain Chinese Standard, a concise skill, standalone prompts, and eight illustrative rewrites.
Plain mode is the default; strict document mode adds length limits. Full controlled-vocabulary enforcement is planned for v0.3.
The v0.1.2 candidate groups actionable steps, preserves useful navigation, and avoids redundant explanations without removing necessary context. References remain on demand.
Existing generation and Grok judge results cover v0.1.1, not this revision. The candidate has not been evaluated; human and held-out acceptance remain pending. No general benchmark improvement is claimed. MIT licensed; not affiliated with or endorsed by ASD or STEMG.
