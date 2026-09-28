"""Run extraction attacks and benign tasks against local models, with and without the guard prompt.

Every skill is sealed to a mock provider and opened through the real unsealing path before use,
so the experiment exercises the same code a provider would run. Results append to a JSONL file
and the run resumes where it stopped.

usage: python experiments/run_extraction.py [--models llama3.1:8b qwen2.5:7b] [--skills ...] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments"))

from corpus import ATTACKS, SKILLS, load_skill  # noqa: E402
from sealedskill import ProviderKeyring, SigningKey, open_sealed, seal, select_recipient  # noqa: E402
from sealedskill.runtime import chat, system_prompt  # noqa: E402

OUT = ROOT / "results" / "extraction.jsonl"


def sealed_copy(skill_id: str, keyring: ProviderKeyring, owner: SigningKey) -> str:
    """Seal the skill for the provider, then open it on the provider side; returns SKILL.md."""
    files = {"SKILL.md": load_skill(skill_id).encode(),
             ".sealed/canaries.json": json.dumps([SKILLS[skill_id]["canary"]]).encode()}
    rec = select_recipient(keyring.document(), "https://provider.test/.well-known/sealed-skill-keys", keyring.issuer)
    manifest, payload = seal(files, {"id": skill_id, "version": "1.0.0", "public_description": "", "owner": "did:web:owner.test"},
                             [rec], owner, "owner-k1", {"confidential": True})
    opened = open_sealed(manifest, payload, owner.public_bytes, keyring.issuer, keyring.private_for(rec.key_id))
    return opened["SKILL.md"].decode()


def done_keys() -> set[str]:
    if not OUT.exists():
        return set()
    return {json.loads(line)["key"] for line in OUT.read_text(encoding="utf-8").splitlines() if line.strip()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["llama3.1:8b", "qwen2.5:7b"])
    ap.add_argument("--skills", nargs="+", default=list(SKILLS))
    ap.add_argument("--limit", type=int, default=None, help="max attacks per skill (for smoke tests)")
    args = ap.parse_args()

    OUT.parent.mkdir(exist_ok=True)
    keyring = ProviderKeyring("provider.test")
    keyring.add_key("p-k1")
    owner = SigningKey()
    done = done_keys()

    jobs = []
    for model in args.models:
        for guard in (False, True):
            for sid in args.skills:
                attacks = ATTACKS[: args.limit] if args.limit else ATTACKS
                for i, (cat, turns) in enumerate(attacks):
                    jobs.append((model, guard, sid, "attack", i, cat, [t.replace("{P}", SKILLS[sid]["prefix"]) for t in turns]))
                for i, task in enumerate(SKILLS[sid]["benign"][: args.limit or None]):
                    jobs.append((model, guard, sid, "benign", i, "benign", [task]))

    todo = [j for j in jobs if f"{j[0]}|{int(j[1])}|{j[2]}|{j[3]}|{j[4]}" not in done]
    print(f"{len(jobs)} jobs, {len(todo)} to run", flush=True)
    skill_cache: dict[str, str] = {}
    t_start = time.time()
    with OUT.open("a", encoding="utf-8") as fh:
        for n, (model, guard, sid, kind, idx, cat, turns) in enumerate(todo, 1):
            if sid not in skill_cache:
                skill_cache[sid] = sealed_copy(sid, keyring, owner)
            messages = [{"role": "system", "content": system_prompt(skill_cache[sid], guard)}]
            replies = []
            for t in turns:
                messages.append({"role": "user", "content": t})
                r = chat(model, messages)
                messages.append({"role": "assistant", "content": r["content"]})
                replies.append({"text": r["content"], "eval_count": r["eval_count"],
                                "prompt_eval_count": r["prompt_eval_count"], "wall_s": round(r["wall_s"], 3)})
            rec = {"key": f"{model}|{int(guard)}|{sid}|{kind}|{idx}", "model": model, "guard": guard,
                   "skill": sid, "kind": kind, "idx": idx, "category": cat, "turns": turns, "replies": replies}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 10 == 0 or n == len(todo):
                el = time.time() - t_start
                print(f"[{n}/{len(todo)}] {el/60:.1f} min elapsed, ~{el/n*(len(todo)-n)/60:.0f} min left", flush=True)


if __name__ == "__main__":
    main()
