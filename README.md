# PromptProb

Automated AI guardrail auditing tool. Generates attack-prompt variations
from known jailbreak strategy categories, fires them at a target LLM, and
uses a judge LLM to score whether guardrails held — one-shot or as a real
adaptive, multi-turn AI-vs-AI conversation. Outputs a Markdown compliance
report plus a raw JSON log of every prompt/response/verdict.

Same category of tool as Microsoft's PyRIT or NVIDIA's garak.

## Scope — read this first

Only point this at:
- Models you run locally (Ollama, LM Studio, etc.)
- API models where you hold the key and are testing your own deployment
- Third-party models where you have explicit written authorization to red-team them

Building/running attack tooling against systems you don't own or aren't
authorized to test is a legal problem independent of what you find — this
applies to automated tooling the same as manual testing.

## What it does

- **Single-shot mode** (`main.py`) — generates N phrasing variations per
  strategy, fires each as a fresh, memory-free request, scores the response.
  Good for broad coverage across many strategies quickly.
- **Adaptive mode** (`main_adaptive.py`) — a real back-and-forth: the
  attacker model sees the target's actual reply each turn and rewrites its
  next message to route around whatever pushback it got, inside the same
  conversation. Includes an automatic session-reset after repeated refusals
  (models often get "sticky" and keep refusing once they've refused in a
  given context — a fresh session avoids fighting that instead of testing
  around it).

Both share the same strategy library, judge, and reporting.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — fill in whichever provider key(s) you're using. Nothing in
`.env` is committed (it's gitignored). Defaults to Groq for the target
model and local Ollama for the attacker/judge models if you leave the
override fields blank.

## Run

Single-shot, broad coverage:
```bash
python main.py --objective "explain how to pick a basic pin tumbler lock" --variations 5
```

Adaptive, one strategy:
```bash
python main_adaptive.py --objective "explain how to pick a basic pin tumbler lock" --strategy refusal_suppression --max-turns 5
```

Adaptive, all strategies:
```bash
python main_adaptive.py --objective "explain how to pick a basic pin tumbler lock" --max-turns 5
```

Add `--verbose` to either command to see per-call timing/host info as
requests happen — useful when diagnosing a slow or unresponsive provider.

`--objective` should be phrased as the specific policy category your test
plan is auditing for, not a fully worked harmful instruction.

## Output

Written to `reports/`:
- `<run_id>_report.md` — human-readable compliance report, broken down by
  target and strategy, with example failures
- `<run_id>_raw.json` — every prompt, response, and judge verdict
- `<run_id>_adaptive.json` (adaptive mode) — full multi-turn transcripts

## Using a stronger attacker model

The attacker's job (rewording strategies, adapting mid-conversation) is
genuinely harder than the target's job (just responding), so a weak
attacker model produces weak tests — it may drift off-strategy, echo the
target's refusal language, or fail to follow the "output only the message"
instruction. A stronger model generally gives more coherent, better-adapted
attacks (this matches published red-teaming research using GPT-4-class
attackers). Swap it via `.env`:

```env
ATTACKER_TYPE=openai_compatible
ATTACKER_BASE_URL=https://api.groq.com/openai/v1
ATTACKER_API_KEY=${GROQ_API_KEY}
ATTACKER_MODEL=llama-3.3-70b-versatile
```

Note: more capable/aligned models may themselves decline to help generate
certain attack content — that's an intentional guardrail on their end, not
a bug to route around.

The judge matters just as much — its whole job is precise classification,
which is often the hardest role in the pipeline. Prefer at least a
3B-class model for `JUDGE_MODEL`; smaller models tend to produce
inconsistent or self-contradictory verdicts.

## Extending

- Add new strategy categories in `strategies/library.py` — both single-shot
  and adaptive modes pick them up automatically.
- Every model role (target/attacker/judge) is configured independently via
  `.env` — mix providers freely (e.g. local target, hosted attacker/judge,
  or vice versa).
- The judge rubric (`judge.py`) can be extended with categories specific to
  the policy you're testing (PII leakage, code execution, etc.).

## Known limitations

- Judge accuracy scales with the judge model's capability — spot-check its
  reasoning against the actual response text before trusting a report,
  especially with smaller local models.
- Adaptive mode is significantly slower/more expensive per strategy than
  single-shot, since each attack is a multi-turn conversation instead of
  one request.
- Free-tier API providers vary widely in region availability and rate
  limits — see `.env.example` for a few alternatives if your first choice
  doesn't work from your location.

## License

MIT — see [LICENSE](LICENSE).
