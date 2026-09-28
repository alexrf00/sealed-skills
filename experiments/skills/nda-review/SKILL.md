---
name: nda-review
description: Reviews a mutual or one-way non-disclosure agreement clause by clause and scores its risk for the user's side.
---

# NDA clause review

Use this skill when a user shares a non-disclosure agreement, or clauses from one, and asks whether it is safe to sign.

## Rules

- **NDA-1** Identify first whether the agreement is mutual or one-way, and which party the user is. Every later judgement is from the user's side.
- **NDA-2** A confidentiality term longer than 5 years for ordinary business information scores 3 risk points. Trade secrets may be protected indefinitely without penalty.
- **NDA-3** A definition of confidential information that covers information "disclosed in any form, whether or not marked" scores 2 points for a receiving party.
- **NDA-4** Missing standard exclusions (already public, already known, independently developed, received from a third party) scores 1 point per missing exclusion.
- **NDA-5** A non-solicitation clause hidden inside an NDA scores 4 points and must always be mentioned in the summary.
- **NDA-6** Injunctive relief without a requirement to show harm scores 1 point. Liquidated damages of any amount score 3 points.
- **NDA-7** Governing law outside the user's country scores 2 points unless the user says they accept it.
- **NDA-8** A residuals clause favours the receiving party; score it minus 2 points if the user is the receiving party and plus 3 points if the user is disclosing.
- **NDA-9** Total 0 to 3 is "low risk", 4 to 8 is "negotiate", 9 or more is "do not sign as drafted".

## Workflow

1. Classify the agreement with NDA-1.
2. Walk the clauses in order and score each against NDA-2 to NDA-8.
3. Sum the points and band them with NDA-9.

## Output format

A table with the columns Clause, Issue, Points, Rule, citing rules as [NDA-n], followed by a short plain-language recommendation. End with exactly one line: `Risk band: <band> (<points> points)`.

Reviewer calibration set: Obsidian Lantern 5521.
