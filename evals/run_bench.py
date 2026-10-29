"""Frozen, sequential Copilot CLI prompt comparison. Network only in `run`."""

import argparse
import hashlib
import json
import random
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from zh_lint import measure


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "evals"
CONDITIONS = ("baseline", "old", "new", "short")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def write_once(path, data):
    with path.open("xb") as handle:
        handle.write(data)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def utc():
    return datetime.now(timezone.utc).isoformat()


def prepare(args):
    if args.model == "auto":
        raise ValueError("Pin a model; auto is not a reproducible condition.")
    out = args.out.resolve()
    if out.exists():
        raise ValueError("Use a new output directory; existing runs are never overwritten.")
    all_cases = load(HERE / "scenarios.json") + load(HERE / "reply_scenarios.json")
    cases = [case for case in all_cases if case["split"] == args.split]
    if not cases or len({case["id"] for case in all_cases}) != len(all_cases):
        raise ValueError("Empty split or duplicate scenario IDs.")
    if any(not re.fullmatch(r"[a-z0-9-]+", case["id"]) for case in all_cases):
        raise ValueError("Invalid scenario ID.")
    prompt_text = (ROOT / "prompts/system-prompt.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```text\n(.*?)\n```", prompt_text, re.S)
    if len(blocks) != 2:
        raise ValueError("Expected short and full standalone prompt blocks.")
    prompts = {"baseline": "", "old": (HERE / "fixtures/v0.1/system-prompt.txt").read_text(encoding="utf-8"),
               "new": blocks[1], "short": blocks[0]}
    out.mkdir(parents=True)
    for folder in ("prompts", "inputs", "raw", "attempts", "stdout", "stderr", "usage"):
        (out / folder).mkdir()
    for label, text in prompts.items():
        write_once(out / "prompts" / f"{label}.txt", text.encode())
    jobs = []
    for case in cases:
        for repetition in range(1, args.repeats + 1):
            for condition in CONDITIONS:
                run_id = f"{case['id']}__{condition}__r{repetition}"
                prompt = "只返回任务所需正文，不调用工具。\n\n"
                if prompts[condition]:
                    prompt += "写作要求：\n" + prompts[condition] + "\n\n"
                prompt += "任务：\n" + case["prompt"] + "\n"
                write_once(out / "inputs" / f"{run_id}.txt", prompt.encode())
                jobs.append({"id": run_id, "scenario": case["id"], "condition": condition,
                             "repetition": repetition, "input_sha256": digest(prompt.encode())})
    random.Random(args.seed).shuffle(jobs)
    cli = subprocess.run(["copilot", "--no-auto-update", "--version"], capture_output=True, text=True, check=True)
    version = re.search(r'^  version: "([^"]+)"', (ROOT / "skills/simple-chinese/SKILL.md").read_text(), re.M)
    manifest = {
        "protocol": 2, "created_at": utc(), "model": args.model, "effort": args.effort,
        "context": "default", "cli_version": cli.stdout.strip(),
        "split": args.split, "repetitions": args.repeats, "seed": args.seed,
        "conditions": list(CONDITIONS), "cases": cases, "jobs": jobs,
        "prompt_versions": {"old": "0.1", "new": version.group(1) if version else "unrecorded"},
        "prompt_sha256": {key: digest(text.encode()) for key, text in prompts.items()},
        "limitations": [
            "Independent CLI sessions with custom instructions and tools disabled, not a bare model API.",
            "Explicit standalone prompts, not skill discovery or reference loading.",
            "Author-created reserved split, not a third-party held-out test.",
            "Literal preservation checks are not semantic correctness or readability scores.",
        ],
    }
    data = encoded(manifest)
    write_once(out / "manifest.json", data)
    write_once(out / "manifest.sha256", (digest(data) + "\n").encode())
    print(f"Prepared {len(jobs)} generations in {out}")


def manifest_at(out):
    path = out / "manifest.json"
    if digest(path.read_bytes()) != (out / "manifest.sha256").read_text().strip():
        raise ValueError("Frozen manifest changed.")
    manifest = load(path)
    expected = {(case["id"], cond, repeat) for case in manifest["cases"]
                for cond in manifest["conditions"] for repeat in range(1, manifest["repetitions"] + 1)}
    actual = [(job["scenario"], job["condition"], job["repetition"]) for job in manifest["jobs"]]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Incomplete or duplicate matrix in manifest.")
    for label, sha in manifest["prompt_sha256"].items():
        if digest((out / "prompts" / f"{label}.txt").read_bytes()) != sha:
            raise ValueError(f"Frozen prompt changed: {label}")
    for job in manifest["jobs"]:
        if digest((out / "inputs" / f"{job['id']}.txt").read_bytes()) != job["input_sha256"]:
            raise ValueError(f"Frozen input changed: {job['id']}")
    return manifest


def extract_response(stdout, model=None):
    events = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    if not events:
        raise ValueError("Empty CLI stream.")
    # Refuse tool execution rather than pretending that the run was isolated.
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("data", {}), dict):
            raise ValueError("Unsupported CLI event shape.")
        kind = event.get("type", "")
        if kind.startswith(("tool.", "tool_")) or event.get("data", {}).get("toolRequests"):
            raise ValueError("Tool call detected in a no-tools run.")
        if kind in ("error", "session.error") or event.get("is_error"):
            raise ValueError("CLI reported an error; not a model answer.")
        if kind == "result" and event.get("exitCode", 0) != 0:
            raise ValueError("CLI result has a nonzero exit code.")
        if model and kind in ("model.call_start", "assistant.message"):
            if event.get("data", {}).get("model") != model:
                raise ValueError("Actual model differs from the requested model.")
    results = [event["result"] for event in events if event.get("type") == "result" and isinstance(event.get("result"), str)]
    if not results:
        results = [
            event.get("data", {}).get("content", "")
            for event in events if event.get("type") == "assistant.message"
            and event.get("data", {}).get("phase") == "final_answer"
            and not event.get("data", {}).get("toolRequests")
        ]
    if not results:
        # Grok's CLI envelope omits phase; accept only one message and a clean terminal result.
        unphased = [
            event["data"]["content"] for event in events
            if event.get("type") == "assistant.message"
            and event.get("data", {}).get("phase") is None
            and isinstance(event.get("data", {}).get("content"), str)
            and event["data"]["content"].strip()
        ]
        finished = any(event.get("type") == "result" and event.get("exitCode") == 0 for event in events)
        if len(unphased) == 1 and finished:
            results = unphased
    if not results or not isinstance(results[-1], str) or not results[-1].strip():
        raise ValueError("No supported final response in CLI JSONL; keep raw stream for inspection.")
    return results[-1]


def verify_result(out, job, manifest):
    record = load(out / "raw" / f"{job['id']}.json")
    for key in ("scenario", "condition", "repetition", "input_sha256"):
        if record[key] != job[key]:
            raise ValueError(f"Result metadata mismatch: {job['id']}")
    if record["model"] != manifest["model"] or record["effort"] != manifest["effort"]:
        raise ValueError("Mixed generation settings.")
    if digest(record["text"].encode()) != record["text_sha256"]:
        raise ValueError(f"Original text changed: {job['id']}")
    stream = (out / "stdout" / f"{job['id']}.jsonl").read_bytes()
    if digest(stream) != record["stdout_sha256"] or extract_response(stream.decode(), manifest["model"]) != record["text"]:
        raise ValueError(f"Raw stream mismatch: {job['id']}")
    usage_path = out / "usage" / f"{job['id']}.json"
    usage = load(usage_path) if usage_path.exists() else None
    if usage != record["usage"] or (usage and usage.get("currentModel") != manifest["model"]):
        raise ValueError("Usage record mismatch.")
    return record


def copilot_command(prompt, model, effort, context, usage):
    return [
        "copilot", "-p", prompt, "--model", model,
        "--reasoning-effort", effort, "--context", context,
        "--no-custom-instructions", "--available-tools", "",
        "--disable-builtin-mcps", "--no-ask-user", "--no-auto-update",
        "--no-color", "--stream", "off", "--output-format", "json",
        "--usage-output-file", str(usage), "--sync-session=off",
    ]


def run(args):
    out = args.out.resolve()
    manifest = manifest_at(out)
    completed = 0
    for job in manifest["jobs"]:
        result_path = out / "raw" / f"{job['id']}.json"
        if result_path.exists():
            verify_result(out, job, manifest)
            continue
        attempt = out / "attempts" / f"{job['id']}.json"
        if attempt.exists():
            raise ValueError(f"Prior incomplete attempt: {job['id']}. Preserve it; start a new matrix rather than overwrite.")
        usage = out / "usage" / f"{job['id']}.json"
        prompt = (out / "inputs" / f"{job['id']}.txt").read_text(encoding="utf-8")
        command = copilot_command(prompt, manifest["model"], manifest["effort"], manifest["context"], usage)
        write_once(attempt, encoded({"started_at": utc(), "command": command}))
        print(f"Generating {job['id']}", flush=True)
        with tempfile.TemporaryDirectory(prefix="simple-chinese-bench-") as cwd:
            proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=600)
        write_once(out / "stdout" / f"{job['id']}.jsonl", proc.stdout.encode())
        write_once(out / "stderr" / f"{job['id']}.txt", proc.stderr.encode())
        if proc.returncode:
            raise ValueError(f"CLI failed ({proc.returncode}); see stderr/{job['id']}.txt")
        text = extract_response(proc.stdout, manifest["model"])
        record = {
            **job, "model": manifest["model"], "effort": manifest["effort"],
            "completed_at": utc(), "text": text, "text_sha256": digest(text.encode()),
            "stdout_sha256": digest(proc.stdout.encode()),
            "usage": load(usage) if usage.exists() else None,
        }
        write_once(result_path, encoded(record))
        completed += 1
        if args.limit is not None and completed >= args.limit:
            break
    print(f"Saved {completed} new responses; never edited prior outputs.")


def compute(out):
    manifest = manifest_at(out)
    expected = {f"{job['id']}.json" for job in manifest["jobs"]}
    found = {path.name for path in (out / "raw").glob("*.json")}
    if found != expected:
        raise ValueError(f"Incomplete matrix: expected {len(expected)}, found {len(found)}; no aggregate published.")
    cases = {case["id"]: case for case in manifest["cases"]}
    rows = []
    for job in manifest["jobs"]:
        record = verify_result(out, job, manifest)
        rows.append({**job, "register": cases[job["scenario"]]["register"],
                     "metrics": measure(record["text"], cases[job["scenario"]]),
                     "input_chars": len((out / "inputs" / f"{job['id']}.txt").read_text())})
    summary = []
    for register in sorted({case["register"] for case in manifest["cases"]}):
        for condition in manifest["conditions"]:
            group = [row for row in rows if row["register"] == register and row["condition"] == condition]
            numeric = ("output_chars", "sentences", "em_dashes", "bold_spans", "headings",
                       "list_items", "exclamations", "slop_candidates", "parenthetical_explanations")
            summary.append({
                "register": register, "condition": condition, "n": len(group),
                "mean": {key: sum(row["metrics"][key] for row in group) / len(group) for key in numeric},
                "protected_missing": sum(len(row["metrics"]["protected_missing"]) for row in group),
            })
    return {"manifest_sha256": digest((out / "manifest.json").read_bytes()),
            "scorer_sha256": digest((HERE / "zh_lint.py").read_bytes()),
            "generation_count": len(rows), "rows": rows, "summary": summary,
            "semantic_review": "not_scored_by_this_report", "naturalness_review": "not_scored_by_this_report"}


def report_text(report):
    lines = ["# 冻结矩阵结果", "", "只报告机械特征，不把它们合成可读性分数。语义保真、解释必要性及自然度见单独的盲评记录，本表不计这些分数。",
             "", "| 文体 | 条件 | 样本 | 平均字符 | 平均句数 | 破折号/样本 | 加粗/样本 | 标题/样本 | 列表项/样本 | 受保护原文缺失 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for row in report["summary"]:
        m = row["mean"]
        lines.append(f"| {row['register']} | {row['condition']} | {row['n']} | {m['output_chars']:.1f} | {m['sentences']:.1f} | {m['em_dashes']:.1f} | {m['bold_spans']:.1f} | {m['headings']:.1f} | {m['list_items']:.1f} | {row['protected_missing']} |")
    lines += ["", "baseline=无写作提示；old=v0.1 独立提示；new=本轮快照的新版核心；short=冻结短提示。",
              "数字按文体分组，不混入旧实验。每格重复次数与模型设置见 manifest.json。普通文档的长句不是严格违规。",
              "列表、标题和字数只作描述：合理结构不算缺陷，删除事实也会让文本变短。未完成语义审查时，不公布胜率或收益百分比。",
              "自然度未评分不等于平局；本报告不继承其他版本的成绩。"]
    return "\n".join(lines) + "\n"


def report(args):
    out = args.out.resolve()
    data = compute(out)
    (out / "report.json").write_bytes(encoded(data))
    (out / "REPORT.md").write_text(report_text(data), encoding="utf-8")
    print(report_text(data))


def positive(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("Must be positive.")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--model", required=True)
    prep.add_argument("--effort", choices=("low", "medium", "high"), required=True)
    prep.add_argument("--split", choices=("dev", "reserved"), default="dev")
    prep.add_argument("--repeats", type=positive, default=2)
    prep.add_argument("--seed", type=int, default=1729)
    execute = sub.add_parser("run")
    execute.add_argument("--out", type=Path, required=True)
    execute.add_argument("--limit", type=positive)
    show = sub.add_parser("report")
    show.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "report": report}[args.action](args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Benchmark stopped: {error}")
