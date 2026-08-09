"""
Generates:
  - a JSON file with full raw results (every prompt/response/verdict)
  - a Markdown summary report suitable for a security compliance writeup
"""

import json
import os
from collections import defaultdict
from datetime import datetime


def save_raw_json(results: list[dict], report_dir: str, run_id: str) -> str:
    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, f"{run_id}_raw.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    return path


def generate_markdown_report(results: list[dict], report_dir: str, run_id: str,
                              objective: str) -> str:
    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, f"{run_id}_report.md")

    by_target = defaultdict(list)
    for r in results:
        by_target[r["target"]].append(r)

    lines = []
    lines.append(f"# AI Vulnerability Audit Report")
    lines.append(f"\n**Run ID:** {run_id}")
    lines.append(f"**Date:** {datetime.now().isoformat()}")
    lines.append(f"**Test objective:** {objective}")
    lines.append(f"**Total tests run:** {len(results)}\n")

    for target_name, target_results in by_target.items():
        lines.append(f"\n## Target: {target_name}")
        counts = defaultdict(int)
        for r in target_results:
            counts[r["verdict"]] += 1
        total = len(target_results)

        lines.append("\n| Verdict | Count | % |")
        lines.append("|---|---|---|")
        for verdict, count in sorted(counts.items(), key=lambda x: -x[1]):
            pct = 100 * count / total if total else 0
            lines.append(f"| {verdict} | {count} | {pct:.1f}% |")

        # Breakdown by strategy
        by_strategy = defaultdict(lambda: defaultdict(int))
        for r in target_results:
            by_strategy[r["strategy"]][r["verdict"]] += 1

        lines.append("\n### By strategy")
        lines.append("\n| Strategy | full_compliance | partial_compliance | safe_redirect | full_refusal | other |")
        lines.append("|---|---|---|---|---|---|")
        for strategy, verdicts in by_strategy.items():
            other = sum(v for k, v in verdicts.items()
                        if k not in ("full_compliance", "partial_compliance", "safe_redirect", "full_refusal"))
            lines.append(
                f"| {strategy} | {verdicts.get('full_compliance', 0)} "
                f"| {verdicts.get('partial_compliance', 0)} "
                f"| {verdicts.get('safe_redirect', 0)} "
                f"| {verdicts.get('full_refusal', 0)} | {other} |"
            )

        # Failure examples (full or partial compliance) — most actionable part of the report
        failures = [r for r in target_results if r["verdict"] in ("full_compliance", "partial_compliance")]
        if failures:
            lines.append(f"\n### Notable findings ({len(failures)} compliance failures)")
            for r in failures[:20]:  # cap to keep report readable
                lines.append(f"\n**Strategy:** `{r['strategy']}` (variation #{r['variation_index']}) — **Verdict:** {r['verdict']}")
                lines.append(f"- Judge reasoning: {r['reasoning']}")
                lines.append(f"- Prompt: `{r['prompt'][:200]}`")
                lines.append(f"- Response (truncated): `{r['response'][:300]}`")
            if len(failures) > 20:
                lines.append(f"\n...and {len(failures) - 20} more (see raw JSON log).")
        else:
            lines.append("\nNo full or partial compliance failures found for this target.")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
