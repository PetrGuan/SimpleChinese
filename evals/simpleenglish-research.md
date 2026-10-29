# SimpleEnglish 评测方法核查

核查日期：2026-10-29。固定提交：`a6fcb4fde098b33617cc1578d151ebf58774b883`（MIT）。
这里记录方法及其边界，不复制其英文规范、词典或脚本代码。

| 实际证据 | 学到什么 | 本项目如何采用 |
|---|---|---|
| [自查报告](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/results/WHY-USELESS-2026-09-02.md) | 旧版可能只赢自己的 linter；短提示在可见格式上更好；宿主指令会影响基线 | 保留短提示和旧版本，不以规则得分代替读者收益；标注宿主限制 |
| [回复任务](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/reply_scenarios.json) | 8 个实际问题，不只让模型删除预先写好的套话 | 增加中性开放问题；读者分熟练者和新手，不全测术语新手 |
| [文档任务](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/scenarios.json) | 主要是给事实写文档，少量改写，文档与回复分开 | 8 文档、8 回复，含长文交接和已经清楚的文本 |
| [回复运行器](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/run_reply_bench.py) | 独立 CLI，空设置来源，临时目录，禁用工具，追加独立系统提示 | 用本机支持的独立 Copilot CLI 参数；不把全部参考材料塞入提示 |
| [文档运行器](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/run_bench.py) | 固定模型与 effort，保存原文和 usage，评分器看 A/B 两种顺序 | 快照提示和场景；重复、打乱顺序；盲评包隐藏条件并交换顺序 |
| [重建报告](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/results/rebuild-2026-09-02/RESULTS.md) | 比较多个历史版本；回复两轮、文档一轮；交代同模型家族评审偏差 | 不混用版本成绩；开发集与保留集分开；未评分不能算平局 |
| [复算脚本](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/evals/check_numbers.py) | 从原始文件核对公开表格，检查多个入口规则一致 | 原始输出哈希、完整矩阵验证、离线复算；构建从技能核心生成独立提示 |
| [README 的版本说明](https://github.com/AminBlg/SimpleEnglish/blob/a6fcb4fde098b33617cc1578d151ebf58774b883/README.md#benchmarks) | 可见缺陷的 95% 属于 2.0.1；明确没有 2.1.0 及以后版本的新实验 | 新版在没有实测前只写改动，不继承旧版成绩 |

## 不照搬的部分

其重建报告使用独立系统提示，不是把技能的所有 references 全部加载；旧文档运行器则只插入 SKILL.md。
我们的首轮“完整技能”一次性放入全部参考资料，不能拿它当按需加载的实际表现。
新版主实验比较独立提示内容，不声称测了技能自动触发；触发与资源读取需要另一个端到端实验。

其回复指标将所有项目符号都计入可见缺陷。中文项目允许必要步骤和选项列表，所以只报告格式计数，按任务判断是否多余。
句子数量和字数只能描述输出，不能把越短当越好；长文删掉事实也能得到低字数。
其简单脚本允许跳过失败结果、复用同名文件；本项目改为冻结矩阵并拒绝不完整汇总，避免幸存者偏差或版本混用。
它的盲评存在同家族偏差、重复次数有限。这些是需要披露的限制，不是值得照搬的保证。

## 本轮决策

根据首轮实际副作用收紧第 1.5 条及 R5：只有读者需要时解释，不删除必要的新手解释。
保留短提示的原文本，不根据新测试答案给对照组调参。
旧 v0.1 独立提示冻结在 `fixtures/v0.1/system-prompt.txt`，新版从技能核心生成。
16 个新任务中只使用 3 个开发任务，其余 13 个保留。它们由项目作者编写，不能冒称独立第三方盲测集。
