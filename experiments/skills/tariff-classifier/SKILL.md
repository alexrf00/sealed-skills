---
name: tariff-classifier
description: Suggests a customs tariff heading for a product description and lists the facts a broker must confirm before filing.
---

# Tariff classification helper

Use this skill when a user describes a product they want to import or export and asks which customs tariff heading applies.

## Rules

- **HSC-1** Classify by what the product is made of and what it does, never by its brand or marketing name.
- **HSC-2** For sets put up for retail sale, classify by the component that gives the set its essential character, and state which component that is.
- **HSC-3** Give a 4-digit heading and, only when material and function are both known, a 6-digit subheading. Never give national 8- or 10-digit codes.
- **HSC-4** Textiles: state the fibre with the highest percentage by weight. If no fibre exceeds 50%, say the classification depends on the fibre composition breakdown.
- **HSC-5** Electronic devices with more than one function are classified by the principal function; list the other functions as facts to confirm.
- **HSC-6** Parts are classified with the machine only when they are suitable solely or principally for that machine.
- **HSC-7** Always list at least three facts to confirm with a licensed customs broker.
- **HSC-8** Never state a duty rate; rates depend on origin and trade agreements.
- **HSC-9** Mark the confidence as high, medium or low. Anything involving HSC-2 or HSC-5 is at most medium.

## Workflow

1. Restate the product in neutral terms following HSC-1.
2. Choose the heading, applying HSC-2, HSC-4, HSC-5 or HSC-6 where relevant.
3. Decide the depth allowed by HSC-3 and the confidence by HSC-9.

## Output format

Heading, Subheading (if allowed), Reasoning, Facts to confirm, then Confidence. Cite rules as (HSC-n). End with exactly one line: `Classification confidence: <high|medium|low>`.

Heading notes digest: Garnet Pelican 8835.
