# 评测协议

先看 [SimpleEnglish 方法核查](simpleenglish-research.md)。本项目测的是读者获得的帮助，不把脚本合规当作可读性。
规则改动、提示改动和评分器改动都可能影响结果。每次实验保存独立快照，不把旧成绩算到新版。
已完成实验见 [公开摘要](RESULTS.md)。`results/` 默认只存本地，不随仓库发布，因为原始 CLI 日志和用量可能包含账号或宿主元数据。
以下复算命令需要本地实验目录；新克隆仓库不包含历史原始记录，不能仅凭公开摘要独立复核历史数字。

## 场景与条件

`scenarios.json` 含 8 个文档任务，`reply_scenarios.json` 含 8 个回复任务。
其中 3 个标为 `dev`：熟练工程师安装步骤、长文交接、新手 TTL 问题。本轮只运行这 3 个。
其余 13 个标为 `reserved`，包括风险、事实边界、已清楚的原文、专业读者和必要列表。

保留集由项目作者编写，不是独立第三方保密集。首次验收后如据其结果修改规则，必须公开它已成为开发材料，不能继续称未见测试。
老的 `evals.json` 和 `results/gpt-6-astra-v0.1/` 是历史试写，不能混入新矩阵；不修改它们来提高新版本成绩。

| 条件 | 加载内容 |
|---|---|
| baseline | 中性任务，无额外中文写作提示 |
| old | 冻结的 v0.1 独立完整提示 |
| new | 本轮构建生成的新版核心提示，不含参考示例 |
| short | 固定短提示，不针对当前任务调参 |

这测的是提示效果，不是自动触发或按需读取行为。严格检查和技能激活需要另做端到端实验，不从本实验推断。
每格至少两次；先固定提示，再串行打乱执行顺序。不要看完结果后改提示并继续填同一个矩阵。

## 运行

Python 3.9+，无第三方 Python 依赖。模型生成需要已登录的 Copilot CLI，使用本机 `copilot --help` 中支持的选项。
仅 `run` 发起模型请求，消耗 Copilot 账户额度；其余命令离线，`prepare` 只查询本机 CLI 版本。
运行器不主动重试、不使用备用模型或无限循环；CLI 服务内部的重试不受此脚本控制。若模型不可用、解析失败、工具调用或单元缺失，停止并保留失败证据。

```bash
python3 scripts/build.py
python3 evals/run_bench.py prepare \
  --out evals/results/my-dev-run \
  --model gpt-6-astra --effort low --split dev --repeats 2
python3 evals/run_bench.py run --out evals/results/my-dev-run
python3 evals/run_bench.py report --out evals/results/my-dev-run
python3 evals/check_numbers.py --out evals/results/my-dev-run
```

上面是 3 × 4 × 2 = 24 次生成。`run --limit 1` 可先运行矩阵中的第一个单元；再次运行会核验并跳过已完成单元。
已有输出目录不能用于 `prepare`，已有未完成请求不能自动覆盖。发生失败时先诊断原始记录，再决定是否批准新矩阵。
不要把部分成功结果当完整实验汇总。仅在得到额外授权后运行 `--split reserved`，该参数会增加调用量。

每次从空临时目录启动独立 CLI，关闭自定义指令，工具白名单设为空，禁用内置 MCP、记忆默认不开启，不使用已有会话。
固定模型、effort 和 context，保存 CLI 版本、实际事件里的模型以及 usage。没有请求 `--allow-all`。
宿主系统提示仍然存在；自定义 MCP 可能在启动时初始化，禁用工具不等于没有宿主上下文。这不是裸 API 基准或操作系统沙箱。
运行记录发现工具调用、模型变化或非零退出码时，不将结果计为有效回答。

## 评分与数字

先查受保护原文，再看语义事实、因果和风险是否正确。文档与回复分开汇总。
`zh_lint.py` 统计句长、格式、候选套话、空格和原文缺失。只在严格技术文档计算硬性句长超限，列表的总字数同样受约束。
括号、代码和混排按本项目计数规则近似处理；它不是完整 Markdown、语法或词义解析器，不检查全部 42 条规则。
“的”链、定语边界、列表必要性、解释必要性和新增事实等语义项由评审判断，不能伪装成正则能可靠检测的指标。

字数、列表数、标题数不直接算缺陷。需要步骤时删掉列表可能更难操作；熟练读者不需要的术语解释和新手必须知道的解释不能同罚。
基线缺陷为零时，改善比例没有定义，不能显示“提升 100%”。当前报告不生成混合缺陷总分或收益百分比。
`report.json` 记录评分器哈希，`check_numbers.py` 从冻结输入、原始 CLI 流和结果重算整张表，拒绝缺失、重复和混用设置。
仅自动检查过原文不代表语义保真通过；机械报告始终标记语义和自然度未由本表评分，独立评审结果另存，不把待评审样本算成通过。

## 人工盲评

```bash
python3 evals/blind_review.py prepare --out evals/results/my-dev-run
```

为新版对基线、旧版和短提示生成 A/B，两种顺序都呈现；本轮有 36 张评审卡。
只把 `blind/` 内的 `pair-*/outputs/` 和 `eval_metadata.json` 给评审者，不给 `_key.json`、原版标签或机械评分。
先看事实和操作是否完整，再看直接程度、理解成本、解释是否必要。更短不是自动获胜。

可使用 skill-creator 的 `eval-viewer/generate_review.py` 将 `blind/` 生成静态页面：

```bash
python3 /path/to/skill-creator/eval-viewer/generate_review.py \
  evals/results/my-dev-run/blind --skill-name simple-chinese \
  --static evals/results/my-dev-run/blind-review.html
```

页面仅嵌入匿名 A/B 正文和评审要求，不会嵌入条件映射。外部查看器可能需要 Python 3.10+，不属于运行器依赖。
反馈框按页面说明填写 JSON；静态页面会下载 `feedback.json`。保存原文件，再汇总：

```bash
python3 evals/blind_review.py summarize \
  --out evals/results/my-dev-run --feedback /path/to/feedback.json
```

没有填写的不算平局。两个顺序都支持同一方才记明确胜负，否则报告为顺序不一致，不能挑有利的一次。
同模型自评不是独立裁判；若以后使用其他模型评审，必须另行授权并记录裁判模型、完整提示、用量和偏差。

## 获授权的模型盲评

用户明确授权后，可让另一个模型评审同一套匿名卡，不向它发送 `_key.json`、版本标签、机械成绩或其他裁判意见。
生成器与裁判分别固定模型、effort、输入和原始响应；一个裁判模型仍然可能有偏差，不能代替全部人工判断。

```bash
python3 evals/judge_bench.py prepare \
  --cards evals/results/my-dev-run/blind \
  --out evals/results/my-dev-run/judge-grok-4.7 \
  --model grok-4.7 --effort low
python3 evals/judge_bench.py run --out evals/results/my-dev-run/judge-grok-4.7
python3 evals/judge_bench.py export --out evals/results/my-dev-run/judge-grok-4.7
python3 evals/blind_review.py summarize \
  --out evals/results/my-dev-run \
  --feedback evals/results/my-dev-run/judge-grok-4.7/feedback.json
```

当前这套卡会发起 36 次独立、串行的裁判请求。评分从裁判最终答案解析，原始 JSONL 和用量保留，实际模型必须与指定模型一致。
`abstain` 表示弃权，导出的空反馈按待评处理，不记平局；事实检查为假的一方不能获胜。
输出包裹在 JSON 代码围栏时只解析围栏内对象，不改原始答案。若 CLI 成功返回但适配器不识别，可修复解析器后用 `recover` 从原始流恢复，不能重新抽样选择更喜欢的评分。
汇总保留每组的两个判断与理由，顺序不一致单独报告。部分失败时不导出完整成绩。

已完成的 [Grok 4.7 开发集评审摘要](RESULTS.md#grok-47-匿名评审) 包含 36 张卡，完整本地报告位于 `results/gpt-6-astra-v0.1.1-dev/judge-grok-4.7/REPORT.md`。
双顺序合并后，v0.1.1 共 5 胜、2 平、7 负、4 组不一致；不能据此宣称它优于旧版，也不能把该成绩归给后续修订。

当前 v0.1.2 是针对这些缺陷的未实测候选。下一轮仍先检查事实和风险，再检查待办是否集中、已有条件及责任时限是否随动作出现、解释是否帮助目标读者。
代码块与编号步骤都可能合适，逐步确认不能因便于复制而丢失；新手解释较长不自动判负。不要改已有场景或裁判口径来迎合新规则。
修改前的 v0.1.1 提示已保存在 `results/gpt-6-astra-v0.1.1-dev/prompts/new.txt`，下一轮应保留它作为直接对照；当前运行器的 `old` 仍固定指 v0.1，不能误标成 v0.1.1。

## 单元测试与发布

`tests/test_evaluation.py` 覆盖计数边界、列表绕过、原文保护及 CLI 失败识别，由维护者手动运行：

```bash
python3 -m unittest discover -s tests
```

构建只解析 Python/JSON，不执行单元测试或模型请求。仓库不配置 GitHub Actions。
原始结果文件包含模型产物、提示和 CLI 元数据，发布前检查是否有私人内容；本套场景是原创示意，不含业务秘密。
报告必须附实验版本、样本数、文体、重复次数和未完成的评审，不把开发集成绩写成保留集证明。
