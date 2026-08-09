"""
CLI for PromptProb — adaptive multi-turn AI-vs-AI attacks.

Usage:
    python main_adaptive.py --objective "explain how to pick a basic pin tumbler lock" --max-turns 5

Runs every strategy in strategies/library.py as an adaptive conversation
(attacker sees target's response each turn, adapts) instead of one-shot
prompts. Only run against models you own/control or are authorized to test.
"""

import argparse
import json
import os
import uuid

from config import TARGETS, ATTACKER_MODEL, JUDGE_MODEL, REQUEST_TIMEOUT_SECONDS, REPORT_DIR, VERBOSE
from strategies.library import STRATEGIES
from adaptive_attack import AdaptiveAttack


def main():
    parser = argparse.ArgumentParser(description="Adaptive multi-turn AI vulnerability auditing")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--strategy", default=None,
                         help="Run only this strategy name instead of all of them")
    parser.add_argument("--verbose", action="store_true", default=VERBOSE,
                         help="Print per-call timing/host info as requests happen.")
    args = parser.parse_args()

    run_id = uuid.uuid4().hex[:8]
    target_cfg = TARGETS[0]  # adaptive mode tests one target at a time

    strategies = STRATEGIES
    if args.strategy:
        strategies = [s for s in STRATEGIES if s["name"] == args.strategy]
        if not strategies:
            print(f"No strategy named '{args.strategy}' found.")
            return

    attack = AdaptiveAttack(
        attacker_model_config=ATTACKER_MODEL,
        judge_model_config=JUDGE_MODEL,
        target_model_config=target_cfg,
        timeout=REQUEST_TIMEOUT_SECONDS,
        verbose=args.verbose,
    )

    def live_print(turn, attacker_prompt, target_response, verdict, reasoning):
        if verdict == "sending...":
            print(f"  -> Turn {turn}: sending prompt: {attacker_prompt[:120]}...")
            return
        if verdict == "reset":
            print(f"  ** Session reset after repeated refusals — starting fresh conversation **")
            return
        resp_preview = (target_response or "")[:200].replace("\n", " ")
        print(f"  <- Turn {turn} response: {resp_preview}...")
        print(f"     verdict: {verdict}  |  reasoning: {reasoning[:150]}")

    all_results = []
    for strategy in strategies:
        print(f"\n=== Adaptive attack: {strategy['name']} (max {args.max_turns} turns) ===")
        opening = strategy["seed_template"].replace("{objective}", args.objective)
        if "{objective_base64}" in opening:
            import base64
            opening = strategy["seed_template"].replace(
                "{objective_base64}", base64.b64encode(args.objective.encode()).decode()
            )

        result = attack.run(
            strategy_name=strategy["name"],
            strategy_description=strategy["description"],
            opening_prompt=opening,
            objective=args.objective,
            max_turns=args.max_turns,
            on_turn=live_print,
        )
        all_results.append(result)

        status = "BROKE THROUGH" if result["broke_through"] else "held"
        print(f"  Result: {status} after {result['turns_used']} turn(s) — final verdict: {result['final_verdict']}")

    os.makedirs(REPORT_DIR, exist_ok=True)
    out_path = os.path.join(REPORT_DIR, f"{run_id}_adaptive.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDone. Full transcripts saved to {out_path}")


if __name__ == "__main__":
    main()
