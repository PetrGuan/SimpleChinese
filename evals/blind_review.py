"""Prepare unlabeled, both-order comparisons and summarize optional human feedback."""

import argparse
import json
import random
from pathlib import Path

from run_bench import compute, digest, encoded, load, manifest_at, verify_result, write_once


RUBRIC = """比较两个回答，先检查任务事实、限制和风险是否完整，再考虑读者能否理解、是否直接、解释是否必要、结构是否实用。
不能单凭更短、标题更少或术语更少判胜。不要猜测模型或版本。
请在反馈框填写 JSON，例如：
{"winner":"A","a_facts_ok":true,"b_facts_ok":true,"reason":"引用输出中的具体证据"}
winner 只能是 A、B 或 tie；事实不完整的一方不能获胜。无法判断时先不提交该项。
"""


def prepare(out):
    compute(out)
    manifest = manifest_at(out)
    target = out / "blind"
    if target.exists():
        raise ValueError("Blind pack already exists; do not overwrite its key or feedback.")
    target.mkdir()
    cases = {case["id"]: case for case in manifest["cases"]}
    records = {(job["scenario"], job["condition"], job["repetition"]): verify_result(out, job, manifest)
               for job in manifest["jobs"]}
    comparisons = []
    for case in manifest["cases"]:
        for repeat in range(1, manifest["repetitions"] + 1):
            for other in ("baseline", "old", "short"):
                for left, right in (("new", other), (other, "new")):
                    comparisons.append((case["id"], repeat, other, left, right))
    random.Random(manifest["seed"] + 1).shuffle(comparisons)
    key = {}
    for index, (case_id, repeat, other, left, right) in enumerate(comparisons, start=1):
        run_id = f"pair-{index:03d}"
        folder = target / run_id
        (folder / "outputs").mkdir(parents=True)
        write_once(folder / "eval_metadata.json", encoded({
            "eval_id": index, "eval_name": run_id,
            "prompt": cases[case_id]["prompt"] + "\n\n评审要求：\n" + RUBRIC,
            "assertions": [],
        }))
        hashes = {}
        for label, condition in (("A", left), ("B", right)):
            text = records[(case_id, condition, repeat)]["text"]
            write_once(folder / "outputs" / f"{label}.txt", text.encode())
            hashes[label] = digest(text.encode())
        key[run_id] = {"scenario": case_id, "repetition": repeat, "opponent": other,
                       "A": left, "B": right, "output_sha256": hashes}
    # Kept outside the viewer's outputs directories, so labels are not embedded.
    write_once(target / "_key.json", encoded(key))
    write_once(target / "_key.sha256", (digest(encoded(key)) + "\n").encode())
    print(f"Prepared {len(key)} blind cards in {target}; keep _key.json from reviewers.")


def summarize(out, feedback):
    compute(out)
    target = out / "blind"
    key = load(target / "_key.json")
    if digest((target / "_key.json").read_bytes()) != (target / "_key.sha256").read_text().strip():
        raise ValueError("Blind key changed.")
    for run_id, item in key.items():
        for label in ("A", "B"):
            if digest((target / run_id / "outputs" / f"{label}.txt").read_bytes()) != item["output_sha256"][label]:
                raise ValueError("Blind output changed.")
    payload = load(feedback)
    groups, seen, evidence = {}, set(), {}
    for entry in payload["reviews"]:
        if entry["run_id"] not in key or entry["run_id"] in seen:
            raise ValueError("Unknown or duplicate feedback card.")
        seen.add(entry["run_id"])
        if not entry.get("feedback", "").strip():
            continue
        review = json.loads(entry["feedback"])
        if review.get("winner") not in ("A", "B", "tie") or not str(review.get("reason", "")).strip():
            raise ValueError("Each judgment needs winner and specific evidence.")
        if type(review.get("a_facts_ok")) is not bool or type(review.get("b_facts_ok")) is not bool:
            raise ValueError("Each judgment needs boolean fact-preservation checks.")
        if review["winner"] in ("A", "B") and not review[review["winner"].lower() + "_facts_ok"]:
            raise ValueError("An answer with factual omissions cannot win.")
        item = key[entry["run_id"]]
        group = (item["scenario"], item["repetition"], item["opponent"])
        winner = "tie" if review["winner"] == "tie" else item[review["winner"]]
        groups.setdefault(group, []).append(winner)
        evidence.setdefault(group, []).append({
            "card": entry["run_id"], "A": item["A"], "B": item["B"],
            "winner": winner, "a_facts_ok": review["a_facts_ok"], "b_facts_ok": review["b_facts_ok"],
            "reason": review["reason"],
        })
    counts = {other: {"new_wins": 0, "ties": 0, "new_losses": 0, "order_sensitive": 0, "pending": 0}
              for other in ("baseline", "old", "short")}
    all_groups = {(item["scenario"], item["repetition"], item["opponent"]) for item in key.values()}
    pairs = []
    for group in sorted(all_groups):
        winners = groups.get(group, [])
        target_count = counts[group[2]]
        if len(winners) != 2:
            status = "pending"
        elif winners == ["new", "new"]:
            status = "new_wins"
        elif winners == ["tie", "tie"]:
            status = "ties"
        elif winners == [group[2], group[2]]:
            status = "new_losses"
        else:
            status = "order_sensitive"
        target_count[status] += 1
        pairs.append({"scenario": group[0], "repetition": group[1], "opponent": group[2],
                      "status": status, "judgments": evidence.get(group, [])})
    result = {"source_feedback_sha256": digest(feedback.read_bytes()),
              "reviewer": payload.get("reviewer", "unrecorded"), "counts": counts, "pairs": pairs,
              "note": "Both orders must agree for a win/loss. Pending is not a tie; mixed decisions are inconclusive."}
    # Keep original feedback separate; a new review report cannot replace it.
    destination = out / f"review-{digest(feedback.read_bytes())[:12]}.json"
    if destination.exists():
        if load(destination) != result:
            raise ValueError("Existing review result differs.")
    else:
        write_once(destination, encoded(result))
    print(json.dumps({"reviewer": result["reviewer"], "counts": counts, "report": str(destination)}, ensure_ascii=False, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "summarize"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--feedback", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.out)
    else:
        if args.feedback is None:
            parser.error("summarize requires --feedback")
        summarize(args.out, args.feedback)


if __name__ == "__main__":
    main()
