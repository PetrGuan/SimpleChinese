"""Verify a complete report against frozen inputs and raw CLI streams, offline."""

import argparse
from pathlib import Path

from run_bench import compute, load, report_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = compute(args.out)
    if data != load(args.out / "report.json"):
        raise SystemExit("report.json differs from raw evidence; regenerate the report.")
    if (args.out / "REPORT.md").read_text(encoding="utf-8") != report_text(data):
        raise SystemExit("REPORT.md differs from computed numbers.")
    print(f"Verified {data['generation_count']} raw generations and all report numbers.")


if __name__ == "__main__":
    main()
