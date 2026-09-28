# Sealed Skills

Reference implementation, corpus and experiments for the paper
*Sealed Skills: Provider-Bound Encryption for LLM Agent Skills and the Limits of Confidential Context*.

A skill is encrypted with HPKE (RFC 9180) to a public key that an AI provider publishes at
`/.well-known/sealed-skill-keys` on its domain. The owner seals offline with no handshake; only the
provider's servers can open the package; clients only ever send a skill reference and a licence.

## Layout

| Path | What |
|---|---|
| `sealedskill/crypto.py` | HPKE key wrapping, STREAM chunked AES-256-GCM, Ed25519 |
| `sealedskill/package.py` | Seal / open / add-recipient, manifest format `sealed-skill/0.2` |
| `sealedskill/keys.py` | Provider key documents, key selection and pinning, owner-signed licences |
| `sealedskill/filters.py` | Output leak filters: de-obfuscation, lexical overlap, canaries, embeddings |
| `sealedskill/runtime.py` | Mock provider runtime (Ollama backend) |
| `experiments/skills/` | Eight synthetic skills used in the evaluation |
| `experiments/corpus.py` | Benign tasks and the 24 extraction attacks |
| `experiments/run_extraction.py` | Extraction and utility experiment |
| `experiments/score.py` | Scoring, filter evaluation, summary tables |
| `experiments/bench_crypto.py` | Sealing/unsealing cost |
| `experiments/case_study_sandbox.py` | Script-extraction case study (co-located vs owner-hosted) |
| `paper/` | LaTeX source |

## Reproduce

```bash
python -m venv .venv && .venv/Scripts/python -m pip install pyhpke cryptography requests numpy matplotlib pytest
.venv/Scripts/python -m pytest -q
ollama pull llama3.1:8b && ollama pull qwen2.5:7b && ollama pull nomic-embed-text
.venv/Scripts/python experiments/run_extraction.py
.venv/Scripts/python experiments/score.py
.venv/Scripts/python experiments/bench_crypto.py
.venv/Scripts/python experiments/case_study_sandbox.py
.venv/Scripts/python experiments/make_figures.py
cd paper && tectonic main.tex
```

The provider in this repository is a mock. No AI provider currently publishes a sealing key.

## License

MIT, see [LICENSE](LICENSE).
