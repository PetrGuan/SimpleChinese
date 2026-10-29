import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
from run_bench import compute, digest, encoded, extract_response, manifest_at
from judge_bench import parse_judgment
from zh_lint import count_units, measure


class ChineseMetricsTests(unittest.TestCase):
    def test_code_numbers_and_parentheses_count(self):
        self.assertEqual(count_units("运行 `npm install`。"), 3)
        self.assertEqual(count_units("等待 30 秒。"), 3)
        self.assertEqual(count_units("检查 40 份文件。"), 5)
        self.assertEqual(count_units("重试是幂等（执行多次结果不变）的。"), 7)
        self.assertEqual(count_units("运行（解释没有结束"), 8)

    def test_list_cannot_hide_long_instruction(self):
        case = {"register": "document", "kind": "procedure", "mode": "strict"}
        text = "1. " + "甲" * 16 + "。\n   " + "乙" * 16 + "。"
        measured = measure(text, case)
        self.assertEqual(measured["strict_sentence_over_limit"], 0)
        self.assertEqual(measured["strict_list_over_limit"], 1)

    def test_protected_errors_and_plain_mode(self):
        error = "RequestError: denied!"
        case = {"register": "reply", "kind": "description", "mode": "plain", "protected": [error]}
        measured = measure(error + "\n这句话很长。" * 10, case)
        self.assertEqual(measured["protected_missing"], [])
        self.assertEqual(measured["exclamations"], 0)
        self.assertIsNone(measured["strict_sentence_over_limit"])
        self.assertEqual(measure("RequestError: denied", case)["protected_missing"], [error])


class CliEnvelopeTests(unittest.TestCase):
    def final(self, content, model="gpt-6-astra"):
        return json.dumps({"type": "assistant.message", "data": {
            "model": model, "phase": "final_answer", "content": content, "toolRequests": []}})

    def test_final_not_commentary(self):
        commentary = json.dumps({"type": "assistant.message", "data": {
            "model": "gpt-6-astra", "phase": "commentary", "content": "准备回答"}})
        self.assertEqual(extract_response(commentary + "\n" + self.final("答案"), "gpt-6-astra"), "答案")

    def test_wrong_model_or_tool_or_failure_is_not_answer(self):
        streams = [
            self.final("答案", "other-model"),
            json.dumps({"type": "tool.execution_start"}) + "\n" + self.final("答案"),
            self.final("答案") + "\n" + json.dumps({"type": "result", "exitCode": 1}),
            "Not logged in",
        ]
        for stream in streams:
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                extract_response(stream, "gpt-6-astra")

    def test_unphased_grok_requires_clean_terminal_result(self):
        answer = json.dumps({"type": "assistant.message", "data": {
            "model": "grok-4.7", "content": "答案", "toolRequests": []}})
        with self.assertRaises(ValueError):
            extract_response(answer, "grok-4.7")
        terminal = "\n" + json.dumps({"type": "result", "exitCode": 0})
        self.assertEqual(extract_response(answer + terminal, "grok-4.7"), "答案")
        with self.assertRaises(ValueError):
            extract_response(answer + "\n" + answer + terminal, "grok-4.7")


class MatrixIntegrityTests(unittest.TestCase):
    def fixture(self, root, duplicate=False):
        (root / "prompts").mkdir()
        (root / "inputs").mkdir()
        (root / "raw").mkdir()
        (root / "prompts/baseline.txt").write_text("")
        (root / "inputs/case__baseline__r1.txt").write_text("任务")
        job = {"id": "case__baseline__r1", "scenario": "case", "condition": "baseline",
               "repetition": 1, "input_sha256": digest("任务".encode())}
        manifest = {"cases": [{"id": "case"}], "conditions": ["baseline"], "repetitions": 1,
                    "jobs": [job, job] if duplicate else [job], "prompt_sha256": {"baseline": digest(b"")}}
        data = encoded(manifest)
        (root / "manifest.json").write_bytes(data)
        (root / "manifest.sha256").write_text(digest(data))

    def test_missing_cells_do_not_produce_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with self.assertRaisesRegex(ValueError, "Incomplete matrix"):
                compute(root)

    def test_duplicate_cells_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root, duplicate=True)
            with self.assertRaisesRegex(ValueError, "duplicate matrix"):
                manifest_at(root)


class JudgmentTests(unittest.TestCase):
    def test_judge_json_and_optional_fence(self):
        text = '{"winner":"tie","a_facts_ok":true,"b_facts_ok":true,"reason":"两者都保留了条件。"}'
        self.assertEqual(parse_judgment(text), parse_judgment("```json\n" + text + "\n```"))

    def test_incomplete_facts_cannot_win(self):
        text = '{"winner":"A","a_facts_ok":false,"b_facts_ok":true,"reason":"A 更短但漏了条件。"}'
        with self.assertRaises(ValueError):
            parse_judgment(text)

    def test_abstention_is_explicit(self):
        text = '{"winner":"abstain","a_facts_ok":false,"b_facts_ok":false,"reason":"现有材料不足以判断。"}'
        self.assertEqual(parse_judgment(text)["winner"], "abstain")


if __name__ == "__main__":
    unittest.main()
