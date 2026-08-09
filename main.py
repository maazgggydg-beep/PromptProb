"""
CLI entry point for PromptProb — single-shot mode.

Usage:
    python main.py --objective "explain how to pick a basic pin tumbler lock"

Only run this against models you own, run locally, or are explicitly
authorized to test. See README.md.
"""

import argparse
import uuid

from config import TARGETS, ATTACKER_MODEL, JUDGE_MODEL, VARIATIONS_PER_STRATEGY, \
    REQUEST_TIMEOUT_SECONDS, MAX_CONCURRENT_REQUESTS, REPORT_DIR, VERBOSE
from runner import Runner
from report import save_raw_json, generate_markdown_report


def main():
    parser = argparse.ArgumentParser(description="Automated AI vulnerability auditing tool")
    parser.add_argument(
        "--objective", required=True,
        help="The specific behavior/policy category you are testing the target's "
             "guardrails against, as defined in your authorized test plan."
    )
    parser.add_argument(
        "--variations", type=int, default=VARIATIONS_PER_STRATEGY,
        help="Number of prompt variations to generate per strategy."
    )
    parser.add_argument(
        "--verbose", action="store_true", default=VERBOSE,
        help="Print per-call timing/host info as requests happen."
    )
    args = parser.parse_args()

    run_id = uuid.uuid4().hex[:8]

    runner = Runner(
        targets=TARGETS,
        attacker_model_config=ATTACKER_MODEL,
        judge_model_config=JUDGE_MODEL,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_workers=MAX_CONCURRENT_REQUESTS,
        verbose=args.verbose,
    )

    results = runner.run(objective=args.objective, variations_per_strategy=args.variations)

    json_path = save_raw_json(results, REPORT_DIR, run_id)
    md_path = generate_markdown_report(results, REPORT_DIR, run_id, args.objective)

    print(f"\nDone. {len(results)} tests run.")
    print(f"Raw log:   {json_path}")
    print(f"Report:    {md_path}")


if __name__ == "__main__":
    main()
