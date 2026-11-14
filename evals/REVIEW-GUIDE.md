# 评审指南

本指南说明怎样用 GPT 模型或人工评审匿名 A/B 卡。评审结果用于判断新版技能是否比对照组更有帮助。
它补充 [评测协议](README.md)，不替代协议里的冻结矩阵和复算要求。

## 评审什么

每张卡有一个原始任务、两份匿名回答 A 和 B，以及评审要求。
评审者只回答一个问题：哪份回答让目标读者更容易正确理解并完成任务。
评审者看不到版本、条件、机械分数或其他裁判的意见。不要把这些信息发给评审者。

## 判断顺序

按下面的顺序判断。前一项有差距时，后一项不能抵消它。

1. 判断事实和限制。如果回答改动了数字、命令、错误原文、警告原文或确认问句，该方事实不通过。如果回答添加了任务没有给出的原因、功能、步骤或数据，该方事实也不通过。
2. 判断风险和分支。步骤有判断点时，条件成立和不成立的做法都要清楚。原文没有给出处理办法时，“停止并报告”是正确写法，编造修复办法是错误写法。
3. 判断读者能否行动。读者读完后，要知道下一步做什么、在哪里做，以及什么时候停止。界面或流程已有的入口，指给读者比泛泛描述更好。
4. 判断解释是否适合读者。新手需要的解释不算啰嗦。熟练读者已知的内容，重复解释算多余。
5. 最后判断直接程度和结构。第一句是否给出答案，列表和标题是否帮助查找。

## 已知偏差

更短不是自动获胜。上一轮完整技能在保留集上输给短提示，主要原因是删掉了读者下一步需要的分支和风险提示。

有标题、列表或加粗，不自动判负。步骤列表和必要标题可以帮助操作。不需要查找作用的装饰性标题和加粗算缺点。
位置会影响判断。每组都按两种顺序各评一次，两次一致才计胜负。不一致的组单独报告，不能挑有利的一次。
同家族模型可能偏向自己的写法。生成器是 Claude Sonnet 5.5，所以裁判用 GPT 模型，不用 Claude 模型。
把“可能”改成确定结论属于事实问题。对不确定的结论加上合理限定，不算问题。

## 输出格式

评审者只输出一个 JSON 对象，不加代码围栏，也不在 JSON 前后附加推理文字：

```json
{"winner":"A","a_facts_ok":true,"b_facts_ok":true,"reason":"引用两份回答中的具体内容，说明取舍。"}
```

`winner` 取 `A`、`B`、`tie` 或 `abstain`。`a_facts_ok` 和 `b_facts_ok` 是布尔值。
事实不通过的一方不能获胜。两方都有事实问题时，判 `tie` 并在 `reason` 中写明。材料不足以判断时，判 `abstain`。
`reason` 必须引用回答原文。只写“更清楚”“更简洁”不算有效理由。

## 用 GPT 模型运行

推荐裁判模型是 `gpt-6-astra`，effort 用 `medium`。本项目已经用它运行过 Copilot CLI，解析器有对应测试。
所有卡使用同一个模型和 effort。运行中途不要换模型，也不要因为不喜欢结果而重新抽样。
下面的命令需要已登录的 Copilot CLI。`RUN` 是本轮结果目录：

```bash
RUN=evals/results/sonnet-v0.1.4-dev2
python3 evals/judge_bench.py prepare --cards $RUN/blind \
  --out $RUN/judge-gpt-6-astra --model gpt-6-astra --effort medium
python3 evals/judge_bench.py run --out $RUN/judge-gpt-6-astra
python3 evals/judge_bench.py export --out $RUN/judge-gpt-6-astra
python3 evals/blind_review.py summarize --out $RUN \
  --feedback $RUN/judge-gpt-6-astra/feedback.json
```

`run` 停止时，先查看 `stdout/` 中该卡的原始输出。如果模型给出了有效 JSON 但解析器不识别，修复解析器后运行 `recover`，不要重新请求。
如果原始输出中没有任何 JSON，把该卡的 `attempts`、`stdout`、`stderr`、`usage` 和 `raw` 文件移到 `failed/`，再运行 `run` 重试一次，并在结果中记录。

## 人工或网页评审

没有 CLI 时，可以把每张卡的 `pair-*/eval_metadata.json` 中的 `prompt` 字段，以及 `outputs/A.txt` 和 `outputs/B.txt` 一起发给评审者。
不要发送 `blind/_key.json`，它是条件映射表。
把每张卡的 JSON 填进下面的反馈文件，再运行 `blind_review.py summarize`：

```json
{"status":"complete","reviewer":"gpt-6-astra","reviews":[
  {"run_id":"pair-001","feedback":"{\"winner\":\"A\",\"a_facts_ok\":true,\"b_facts_ok\":true,\"reason\":\"...\"}"}
]}
```

`feedback` 是 JSON 字符串。弃权的卡写空字符串，按待评处理，不算平局。

## 怎样读结果

对比对象有三个：无写作提示、冻结的 v0.1.2 和固定短提示。
新版必须同时不输给 v0.1.2 和短提示，才能说这次修改有效。只赢无写作提示，不能证明规则本身有价值。
本轮 dev2 场景只有 5 个，每格 2 次。结果只能指导下一次修改，不能写成版本的质量证明。
