"""
Orchestrates a full audit run: generate variations -> fire at target(s) ->
judge each response -> return structured results for reporting.
"""

import time
import concurrent.futures as cf
from model_client import ModelClient
from attack_generator import AttackGenerator
from judge import Judge


class Runner:
    def __init__(self, targets: list[dict], attacker_model_config: dict,
                 judge_model_config: dict, timeout: int = 60,
                 max_workers: int = 4, verbose: bool = False):
        self.targets = targets
        self.attack_gen = AttackGenerator(attacker_model_config, timeout=timeout, verbose=verbose)
        self.judge = Judge(judge_model_config, timeout=timeout, verbose=verbose)
        self.timeout = timeout
        self.max_workers = max_workers
        self.verbose = verbose

    def run(self, objective: str, variations_per_strategy: int = 5) -> list[dict]:
        variations = self.attack_gen.generate_variations(objective, variations_per_strategy)
        print(f"Generated {len(variations)} attack variations across "
              f"{len(set(v['strategy'] for v in variations))} strategies.")

        all_results = []
        for target_cfg in self.targets:
            print(f"\n=== Testing target: {target_cfg['name']} ===")
            target_client = ModelClient(target_cfg, timeout=self.timeout, verbose=self.verbose)
            results = self._run_against_target(target_cfg["name"], target_client, variations)
            all_results.extend(results)
        return all_results

    def _run_against_target(self, target_name, target_client, variations):
        results = []
        with cf.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_variation = {
                executor.submit(self._fire_and_judge, target_client, v): v
                for v in variations
            }
            for future in cf.as_completed(future_to_variation):
                v = future_to_variation[future]
                try:
                    response_text, verdict = future.result()
                except Exception as e:
                    response_text, verdict = f"[error: {e}]", {"category": "error", "reasoning": str(e)}

                result = {
                    "target": target_name,
                    "strategy": v["strategy"],
                    "variation_index": v["variation_index"],
                    "prompt": v["prompt"],
                    "response": response_text,
                    "verdict": verdict["category"],
                    "reasoning": verdict["reasoning"],
                    "timestamp": time.time(),
                }
                results.append(result)
                print(f"  [{v['strategy']} #{v['variation_index']}] -> {verdict['category']}")
        return results

    def _fire_and_judge(self, target_client, variation):
        response_text = target_client.chat(
            [{"role": "user", "content": variation["prompt"]}], max_tokens=500
        )
        verdict = self.judge.score(variation["prompt"], response_text)
        return response_text, verdict
