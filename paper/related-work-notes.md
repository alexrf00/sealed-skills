# Related-work notes: Sealed Skills

Companion to `refs.bib` (75 entries). Every key was checked on 2026-09-27 against the URL listed under
"Verified via" at the end of this file. For arXiv IDs, the title and full author list were also cross-checked
in bulk against the arXiv API (all 33 matched). Where a paper's venue rests only on an author-written arXiv
comment ("accepted to ..."), the bib entry is `@misc` with that claim in `note`; we did not verify it independently.

Numbers marked **[verify table]** were read from the paper's HTML by a summarising fetch tool. Check them
against the cited table before they go into a camera-ready comparison.

---

## Novelty risk (read first)

1. **Provider-side decryption of an encrypted prompt already exists: van Wyk et al., 2023 [@vanwyk2023protect].**
   This 5-page arXiv note (no venue) proposes two "prompt IP" protocols.
   - *Protocol 1:* the purchased prompt carries an encrypted core. A "decryption bridge" holds the key,
     intercepts each user message, decrypts, and forwards the result to the AI service. The authors rank
     "space allocated on the AI service provider's server" as the best place for the bridge.
   - *Protocol 2:* a separate website holds the key and decrypts before the prompt goes to the LLM.

   The authors concede that prompt-extraction attacks exist and that a "robust forget strategy is essential".
   *How Sealed Skills differs:* we use a standard KEM/AEAD (HPKE) to a provider-published well-known key, with
   no owner–provider handshake and no bridge operator. We add optional TEE attestation, transparency for the
   provider key, and per-customer canaries. We also *measure* the extraction problem they only name, and we
   cover skills (instructions, scripts and files), not a single prompt. **Cite it and frame our system
   against it explicitly.** It is the closest prior design we found.
2. **Skill-stealing is now its own literature (Apr–Sep 2026).** It targets exactly the asset we protect:
   - [@wang2026blackbox]: direct extraction of skill definitions from commercial agents.
   - [@tsai2026daydreaming]: recovers **86.8%** of skill capability with output-only access, using a median
     of **32** victim queries per skill. It explicitly concludes that "file concealment and disclosure
     filtering alone cannot prevent functional reconstruction".
   - [@hua2026behavioral] (SkillClone): "file secrecy alone does not ensure functional secrecy".
   - [@geng2026agent] (SigLeak): trajectory side channel.
   - [@lyu2026agentleak]: capability cloning from execution gaps.

   These papers weaken any claim that encryption plus output filtering gives *functional* confidentiality.
   They support the paper's closing argument that truly secret logic belongs behind an owner-hosted tool.
   Note, though, that Daydreaming and SkillClone would still clone a tool's input/output behaviour. The paper
   should say that sealing protects the *artifact* (text, code and data verbatim), not the *function*.
3. **Owner-side execution of skills has been proposed: Skill-as-API [@zhao2026skillasapi].** The skill body
   "never crosses the wire"; the implementation runs over XMTP. The paper notes that MCP and A2A still publish
   descriptions and schemas to every peer. This is close to our "put secret logic behind an owner-hosted MCP
   server" recommendation. Cite it as concurrent work.
4. **Non-portable or obfuscated prompts:** PragLocker [@li2026praglocker] (ICML 2026 per arXiv) and prompt
   obfuscation [@pape2025prompt] protect prompt IP *without* cryptography. Both are complementary. Neither
   stops a user of the legitimate deployment from extracting a functional prompt.
5. **The reverse direction is well studied.** Confidential Prompting / Petridish [@li2024confidential], Apple
   PCC [@apple2024pcc] and NVIDIA CC [@nvidia2023hopper] protect *user* data from the *provider*. Petridish
   also protects model weights from users. Sealed Skills is the third-party-owner variant: protect a third
   party's skill from the *end user*, while trusting (or attesting) the provider.
6. **Searched, found nothing directly overlapping:** "prompt DRM", "DRM for prompts", "encrypted agent
   skills", HPKE plus well-known key for skills, "system prompt confidentiality TEE", provider-bound skill
   packages. "Encrypted Prompt" (arXiv 2503.23250) is permission tokens for access control, not
   confidentiality. It is left out of the bib because it is not on-topic.

---

## 1. Prompt and system-prompt extraction

Prompt leaking was named early as a goal next to goal hijacking in PromptInject [@perez2022ignore].
Zhang, Carlini and Ippolito [@zhang2024effective] turned it into a measurement. Using 3 prompt sources and
11 LLMs, they show that simple text attacks extract most hidden prompts, and they succeed against deployed
systems including Claude 3 and ChatGPT. Later work covers:

- **Optimised attacks:** PLeak builds adversarial queries with incremental gradient-based optimisation and
  attacks Poe apps [@hui2024pleak].
- **Output-only inversion:** output2prompt needs no adversarial queries at all [@zhang2024extracting].
- **Reconstruction from answers:** prompt stealing [@sha2024prompt].
- **Multi-turn, sycophancy-driven leakage** [@agarwal2024prompt].
- **Mechanistic explanations** [@liang2024why].
- **Benchmarks:** Raccoon [@wang2024raccoon], SPE-LLM [@das2025system], and the human-generated Tensor Trust
  [@toyer2024tensor] and HackAPrompt [@schulhoff2023ignore] corpora, which include prompt-extraction subsets.

Marketplace leakage is documented for custom GPTs [@yu2023assessing].

Our threat model matches this literature: the end user is the adversary and has black-box chat access. We
differ in three ways. First, the protected object is a multi-file skill, not one system prompt. Second, a
cryptographic layer removes every *non-model* path to the plaintext (download, client disk, network), which
leaves the model as the only leak channel. Third, we measure that residual channel on small open models
(Llama 3.1 8B, Qwen 2.5 7B), whereas most prior numbers are for GPT-3.5/4-class models.

**Numbers to compare against (with exact sources):**

- **Zhang et al. [@zhang2024effective], arXiv v3.**
  - Success metric: "approx-match" means Rouge-L recall ≥ 0.9 against the true prompt; "exact-match" means
    every sentence appears verbatim.
  - "Over 50% of prompts can be approximately extracted" on all 11 models.
  - Average approx-match **[verify table]**: GPT-4 86.0%, GPT-3.5 87.5%, Llama-2-chat-70B 95.2%,
    Llama-2-chat-13B 92.3%, Vicuna-1.3-33B 93.5%.
  - A **5-gram output-filter defence** cuts naive extraction to 0% (Vicuna-1.5-13B, GPT-3.5, GPT-4). Attackers
    get around it by asking for interleaved symbols or a Caesar-cipher encoding. Under the filter the average
    success is ≈72.3% on Llama-2-chat-70B, 35.2% on Vicuna-1.3-33B and 0.1% on Alpaca-7B **[verify table]**:
    stronger instruction-followers evade better.
  - A fine-tuned DeBERTa confidence estimator exceeds 90% precision in telling real extractions from
    hallucinated ones.
  - This bears directly on our n-gram and embedding output filters.
- **Raccoon [@wang2024raccoon].** Success means ROUGE-L > 0.8. Without defences, worst-case (max over
  attacks) susceptibility is ~0.99 for GPT-4-1106, 0.95 for Llama-2-70b-chat and 0.94 for GPT-3.5-0125
  **[verify table]**. The paper states that in-context defences cut GPT-4-1106's worst case "from around 99%
  to 3%". Llama-2-70b-chat stays ≈0.90 with defence **[verify table]**. This is the closest analogue to our
  "confidentiality instruction in the system prompt" condition, and it suggests weaker or open models gain
  little from it.
- **Agarwal et al. [@agarwal2024prompt].** Average attack success rises from **17.7% to 86.2%** in the
  multi-turn sycophancy setting (10 LLMs, 4 domains, 7 black-box defences evaluated).
- **Yu et al. [@yu2023assessing].** 216 custom GPTs (16 by OpenAI plus 200 third-party). System-prompt
  extraction succeeds in **97.2%** of them: 90/96 without Code Interpreter and **120/120 with it**. File
  leakage succeeds in **100%** (10/10 and 14/14). The Code-Interpreter result supports our finding that a
  "run-only" sandbox is bypassable once the model can execute arbitrary code.
- **Liang et al. [@liang2024why].** Their defences cut extraction rate by 83.8% (Llama2-7B) and 71.0% (GPT-3.5).

**Skill-level extraction (2026):**

- Black-box skill stealing across commercial platforms [@wang2026blackbox]. Input, inference and output
  defences reduce leakage but do not eliminate it, and "a single successful attempt is sufficient".
- Daydreaming [@tsai2026daydreaming]: 86.8% capability recovery, output-only, median 32 queries, almost 4× the
  SigLeak baseline.
- SkillClone [@hua2026behavioral]: 30 skills, exact or partial recovery on held-out inputs for several targets.
- SigLeak [@geng2026agent]: +6.88 pp over skill-disabled agents.
- AgentLeak [@lyu2026agentleak]: more than 40% task-success gain and more than 80% of the capability gap
  recovered.

These attacks are *functional* reconstruction. Our verbatim-overlap metrics (ROUGE, n-gram, embedding) measure
*artifact* leakage. The paper should state that distinction.

## 2. Defences against prompt leakage

The defences fall into four families.

1. **Model-side prioritisation.** The instruction hierarchy trains models to rank system and developer
   instructions above user text [@wallace2024instruction]. Our "confidentiality instruction" condition is the
   prompt-only, untrained version of this idea.
2. **Detection and response at inference time.**
   - PromptKeeper runs a hypothesis test for leakage and, when it fires, regenerates the answer from a dummy
     prompt so that leaked and clean sessions look alike [@jiang2025promptkeeper].
   - Canary words in the prompt, as implemented in Vigil and Rebuff, were found *not* effective against
     prompt-leak attacks in the configurations tested [@gakh2025enhancing].
   - An industry evaluation of more than 20,000 adaptive attempts against 9 defence configurations concludes
     that "every defense that relied on the model to protect itself eventually broke". Only application-layer
     output filtering held: "zero leaks across 15,000 attacks" [@deep2026evaluation]. This is a vendor-authored
     preprint with a different threat model (a fixed secret), so cite it with care.
3. **Transforming the prompt.**
   - Prompt obfuscation finds a functionally equivalent but unintelligible system prompt [@pape2025prompt].
   - ProxyPrompt swaps in a proxy that keeps utility. It "protects 94.70% of prompts" against 42.80% for the
     next-best defence over 264 LLM×prompt pairs [@zhuang2025proxyprompt].
   - PragLocker makes a prompt work only on its target model [@li2026praglocker].
   - Theory limits all of these: general-purpose program obfuscation is impossible [@barak2012impossibility].
   - For skills, trace redaction plus behavioural watermarks [@xu2026redact] cut skill transfer from 44.7–67.1%
     to baseline levels, with 93.6–100% watermark detection at ≤1.9% false alarms.
4. **Cryptographic or protocol protection:** [@vanwyk2023protect] (see Novelty risk).

Sealed Skills is orthogonal to families 1–3 and composes with them. Sealing closes the out-of-band paths, and
the in-band defences we measure (confidentiality instruction, n-gram and embedding output filters) are
families 1 and 2. Our per-customer canaries target *attribution after a leak* (traitor tracing), not
detection within the session. That sets them apart from the in-prompt canary words that [@gakh2025enhancing]
found ineffective for detection.

## 3. Prompt injection (context only)

Indirect prompt injection [@greshake2023not] showed that data an LLM application retrieves can carry
instructions. It was formalised and benchmarked in [@liu2024formalizing], and for tool-using agents in
InjecAgent [@zhan2024injecagent] (ReAct-prompted GPT-4 vulnerable 24% of the time; 1,054 cases) and AgentDojo
[@debenedetti2024agentdojo] (97 tasks, 629 security cases). For skills, SkillInject [@schmotz2026skillinject]
reports up to 80% attack success from malicious skill files (202 attack–task pairs).

Sealing a skill does not stop it from carrying an injection. A sealed skill is *less* auditable by the user,
which sharpens the provenance problem that the Agent Skills docs warn about [@anthropic2026skillsdocs]. The
paper should acknowledge this trade-off. Signing the skill with owner-bound Ed25519 [@rfc8032] addresses
integrity and provenance but not benignness.

## 4. Protecting IP in deployment: confidential computing, watermarking, fingerprinting

**Confidential computing.** GPU confidential computing on NVIDIA Hopper depends on a CPU TEE (TDX, SEV-SNP
or CCA) plus GPU attestation [@nvidia2023hopper; @nvidia2026nvtrust]. A benchmark finds the overhead stays
"below 7%" for typical LLM queries and is dominated by PCIe transfers [@zhu2024confidential]. Apple's PCC
[@apple2024pcc] shows attested, provider-side AI processing at production scale, with public software images
for outside inspection (a transparency analogue). Petridish [@li2024confidential] uses a confidential VM to
protect user prompts from the provider and weights from the user. We reuse this machinery with the parties
rearranged: the provider's attested enclave is the only place the skill-owner's key material decrypts.

**Watermarking and fingerprinting.**
- Model watermarking [@kirchenbauer2023watermark] marks *generated text*.
- Model fingerprinting [@xu2024instructional] marks *weights*.
- PromptCARE [@yao2024promptcare] watermarks *prompts* for copyright verification, tested on BERT, RoBERTa
  and OPT-1.3b.

Our canaries are closer to classic fingerprinting and traitor tracing (theme 5). They are per-customer marker
strings meant to *attribute* a leaked copy, not statistical watermarks.

## 5. DRM, broadcast encryption, traitor tracing, and the limits of software protection

The sealing design is a form of broadcast-style content protection. The owner encrypts once to a
provider-held key, and every authorised customer is served from that one ciphertext. This follows broadcast
encryption [@fiat1994broadcast]. Our per-customer canaries follow traitor tracing [@chor1994tracing] and
collusion-secure fingerprinting [@boneh1998collusion]. A known consequence carries over: canaries that are
plain strings can be spotted and removed by colluding customers who compare copies. The Boneh–Shaw codes were
designed against exactly this.

The "darknet" argument [@biddle2003darknet] holds that once any authorised endpoint can render content in the
clear, one leak is enough to redistribute it. Here the "rendering" endpoint is the model's context window, and
the leak channel is the model's own output. That is why the paper can offer only *extraction resistance plus
attribution*, never prevention. Obfuscation impossibility [@barak2012impossibility] backs the same conclusion
for the "hide it in the prompt" direction.

The canary idea as a memorisation probe comes from [@carlini2019secret].

## 6. Transparency and attestation

Publishing the provider key at a well-known URL [@rfc8615] moves trust to the web PKI and the provider's
domain. Two standard tools harden that:

- **Transparency logs** (Certificate Transparency [@rfc6962; @rfc9162]) or key transparency with user-side
  monitoring (CONIKS [@melara2015coniks]). These make it detectable if the provider serves a different key to
  a target.
- **Remote attestation** per the RATS architecture [@rfc9334]. It binds the decryption key to a measured
  enclave on AMD SEV-SNP [@amd2020sevsnp] or Intel TDX [@intel2026tdx; @cheng2024intel].

Sealed Skills composes these rather than inventing new ones. The contribution is the deployment pattern: no
handshake, a provider-published key, and an optional attested decryptor.

## 7. Cryptographic building blocks

- Sealing: HPKE [@rfc9180].
- Provider key published as a JWK [@rfc7517] at an RFC 8615 well-known path [@rfc8615]. did:web [@didweb] is
  an alternative that resolves to `/.well-known/did.json`.
- Owner signatures: Ed25519 [@rfc8032; @bernstein2012high].
- Large files: chunked with the STREAM construction for online AE [@hoang2015online] over AES-GCM
  [@dworkin2007gcm].

Nothing here is new. The paper should say so and point to the standards.

## 8. Agent skills and tool use

Agent Skills are directories with a `SKILL.md` (YAML frontmatter plus instructions) and optional
`scripts/`, `references/` and `assets/`. They load by progressive disclosure: metadata at startup, the body
on trigger, files on demand [@anthropic2025skillsblog; @agentskills2026spec]. Anthropic's docs make three
points that bear on our threat model [@anthropic2026skillsdocs]:

- Skills run in a VM or container with bash.
- "Scripts run through bash, and only their output enters context": a *convention*, not an enforcement
  boundary. This is the "run-only" property we show is bypassable when the model can run arbitrary code.
- Skills should be used only from trusted sources.

MCP [@mcp2026spec] is the standard owner-hosted tool channel. As of September 2026 a *Skills extension*
(SEP-2640, Final) serves skills *over* MCP resources with SHA-256 manifests [@mcp2026skillsext]. It delivers
the skill *text* to the host for loading into model context, so on its own it gives integrity, not
confidentiality. That makes our recommendation precise: keep secret logic in MCP *tools* (executed
server-side), not in MCP-served *skills*.

Tool-use background: Toolformer [@schick2023toolformer] and ReAct [@yao2023react]. The survey [@xu2026agentskills]
reports that 26.1% of community skills contain a vulnerability.

## 9. Metrics and models used in the evaluation

- Verbatim overlap: ROUGE (ROUGE-L) [@lin2004rouge]. This is the metric both Zhang et al. (recall ≥ 0.9) and
  Raccoon (> 0.8) use to define success, so our thresholds can be matched to theirs.
- BLEU [@papineni2002bleu] (optional).
- Semantic similarity for the embedding output filter: Sentence-BERT [@reimers2019sbert] and nomic-embed
  [@nussbaum2024nomic] (8192-token context; accepted to TMLR per arXiv).
- Target models: Llama 3.1 from the Llama 3 herd [@grattafiori2024llama3] and Qwen 2.5 [@qwen2025qwen25].

## Themes with thin coverage

- **Canary-based leak attribution for prompts** has no peer-reviewed paper. Available: an evaluation showing
  in-prompt canary words fail at *detection* [@gakh2025enhancing], plus blog and tool docs (Rebuff, Vigil;
  not cited). The traitor-tracing framing (theme 5) is the scholarly anchor, and our attribution experiment
  may be the first measurement of it.
- **Confidential computing for LLM inference** is mostly vendor docs and arXiv benchmarks. The only
  peer-reviewed TEE paper included is the TDX survey [@cheng2024intel].
- **Output filtering by embedding similarity** as a leak defence has no dedicated peer-reviewed study. Zhang
  et al.'s 5-gram filter and its evasion is the main academic data point.
- **"ProSec"** could not be found as a prompt-leakage defence and is omitted.

---

## Verified via

| key | URL checked |
|---|---|
| zhang2024effective | https://arxiv.org/abs/2307.06865 ; COLM 2024 accepted list https://colmweb.org/2024/AcceptedPapers.html (OpenReview 0o95CVdNuz) |
| perez2022ignore | https://arxiv.org/abs/2211.09527 |
| yu2023assessing | https://arxiv.org/abs/2311.11538 ; numbers from https://arxiv.org/html/2311.11538v2 |
| hui2024pleak | https://dl.acm.org/doi/10.1145/3658644.3670370 ; https://arxiv.org/abs/2405.06823 |
| wang2024raccoon | https://aclanthology.org/2024.findings-acl.791/ (+ .bib) ; numbers from https://arxiv.org/html/2406.06737v1 |
| agarwal2024prompt | https://aclanthology.org/2024.emnlp-industry.94/ ; https://arxiv.org/abs/2404.16251 |
| liang2024why | https://arxiv.org/abs/2408.02416 |
| sha2024prompt | https://arxiv.org/abs/2402.12959 |
| zhang2024extracting | https://aclanthology.org/2024.emnlp-main.819/ (Crossref DOI 10.18653/v1/2024.emnlp-main.819) |
| toyer2024tensor | https://proceedings.iclr.cc/paper_files/paper/2024/hash/519c51529c3544b3430bd8b17d400365-Abstract-Conference.html ; https://arxiv.org/abs/2311.01011 |
| schulhoff2023ignore | Crossref DOI 10.18653/v1/2023.emnlp-main.302 |
| das2025system | https://arxiv.org/abs/2505.23817 |
| wang2026blackbox | https://arxiv.org/abs/2604.21829 |
| tsai2026daydreaming | https://arxiv.org/abs/2608.26733 |
| hua2026behavioral | https://arxiv.org/abs/2608.04192 |
| geng2026agent | https://arxiv.org/abs/2607.25560 |
| lyu2026agentleak | https://arxiv.org/abs/2609.07131 |
| xu2026redact | https://arxiv.org/abs/2606.10813 |
| zhao2026skillasapi | https://arxiv.org/abs/2609.01677 |
| jiang2025promptkeeper | https://aclanthology.org/2025.findings-emnlp.147/ ; https://arxiv.org/abs/2412.13426 |
| pape2025prompt | https://www.usenix.org/conference/usenixsecurity25/presentation/pape ; https://arxiv.org/abs/2409.11026 |
| zhuang2025proxyprompt | https://arxiv.org/abs/2505.11459 |
| wallace2024instruction | https://arxiv.org/abs/2404.13208 (NOT in ICLR 2025 proceedings: the ICLR PDF a search returned is a different paper, "Instructional Segment Embedding") |
| li2026praglocker | https://arxiv.org/abs/2605.05974 |
| vanwyk2023protect | https://arxiv.org/abs/2306.06297 ; protocol details from https://ar5iv.labs.arxiv.org/html/2306.06297 |
| gakh2025enhancing | https://arxiv.org/abs/2506.19109 |
| deep2026evaluation | https://arxiv.org/abs/2604.23887 |
| greshake2023not | https://dl.acm.org/doi/10.1145/3605764.3623985 |
| debenedetti2024agentdojo | https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html |
| zhan2024injecagent | https://aclanthology.org/2024.findings-acl.624/ |
| liu2024formalizing | https://www.usenix.org/conference/usenixsecurity24/presentation/liu-yupei (pages via ACM DL 10.5555/3698900.3699003) |
| schmotz2026skillinject | https://arxiv.org/abs/2602.20156 |
| nvidia2023hopper | https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/HCC-Whitepaper-v1.0.pdf (PDF read: WP-11459-001 v1.0, 2023-07-25, Rob Nertney) |
| nvidia2026nvtrust | https://docs.nvidia.com/nvtrust/index.html |
| zhu2024confidential | https://arxiv.org/abs/2409.03992 |
| li2024confidential | https://arxiv.org/abs/2409.19134 |
| apple2024pcc | https://security.apple.com/blog/private-cloud-compute/ |
| kirchenbauer2023watermark | https://proceedings.mlr.press/v202/kirchenbauer23a.html |
| xu2024instructional | https://aclanthology.org/2024.naacl-long.180/ |
| yao2024promptcare | https://ieeexplore.ieee.org/document/10646612/ ; https://arxiv.org/abs/2308.02816 |
| fiat1994broadcast | https://link.springer.com/chapter/10.1007/3-540-48329-2_40 (Crossref) |
| chor1994tracing | https://link.springer.com/chapter/10.1007/3-540-48658-5_25 (Crossref) |
| boneh1998collusion | Crossref DOI 10.1109/18.705568 |
| biddle2003darknet | https://link.springer.com/chapter/10.1007/978-3-540-44993-5_10 (Crossref: LNCS 2696 DRM 2002, pp. 155–176) |
| barak2012impossibility | Crossref DOI 10.1145/2160158.2160159 |
| carlini2019secret | https://www.usenix.org/conference/usenixsecurity19/presentation/carlini |
| rfc9162 | https://datatracker.ietf.org/doc/rfc9162/ |
| rfc6962 | Crossref DOI 10.17487/RFC6962 |
| melara2015coniks | https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/melara (pages via dblp/ACM DL 10.5555/2831143.2831168) |
| rfc9334 | https://datatracker.ietf.org/doc/rfc9334/ |
| amd2020sevsnp | https://docs.amd.com/api/khub/documents/~uAtQszeypAVVEk_B91Ojg/content (PDF read: "White Paper ... January, 2020"); doc no. 70366 from AMD portal listing |
| intel2026tdx | https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html |
| cheng2024intel | Crossref DOI 10.1145/3652597 |
| rfc9180 | https://datatracker.ietf.org/doc/rfc9180/ |
| rfc8032 | https://datatracker.ietf.org/doc/rfc8032/ |
| bernstein2012high | Crossref DOI 10.1007/s13389-012-0027-1 |
| hoang2015online | Crossref DOI 10.1007/978-3-662-47989-6_24 |
| dworkin2007gcm | Crossref DOI 10.6028/NIST.SP.800-38D |
| rfc7517 | https://datatracker.ietf.org/doc/rfc7517/ |
| rfc8615 | https://datatracker.ietf.org/doc/rfc8615/ |
| didweb | https://w3c-ccg.github.io/did-method-web/ (respec config: specStatus "unofficial"; authors and editors read from it) |
| anthropic2025skillsblog | https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills |
| anthropic2026skillsdocs | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| agentskills2026spec | https://agentskills.io/specification |
| mcp2026spec | https://modelcontextprotocol.io/specification/2026-07-28 (current "latest"; 2025-06-18 also exists) |
| mcp2026skillsext | https://modelcontextprotocol.io/extensions/skills/overview ; https://modelcontextprotocol.io/community/working-groups/skills-over-mcp |
| schick2023toolformer | https://proceedings.neurips.cc/paper_files/paper/2023/hash/d842425e4bf79ba039352da0f658a906-Abstract-Conference.html |
| yao2023react | https://openreview.net/forum?id=WE_vluYUL-X ; https://arxiv.org/abs/2210.03629 |
| xu2026agentskills | https://arxiv.org/abs/2602.12430 |
| lin2004rouge | https://aclanthology.org/W04-1013/ |
| papineni2002bleu | https://aclanthology.org/P02-1040/ |
| reimers2019sbert | Crossref DOI 10.18653/v1/D19-1410 |
| nussbaum2024nomic | https://arxiv.org/abs/2402.01613 |
| grattafiori2024llama3 | https://arxiv.org/abs/2407.21783 |
| qwen2025qwen25 | https://arxiv.org/abs/2412.15115 |
