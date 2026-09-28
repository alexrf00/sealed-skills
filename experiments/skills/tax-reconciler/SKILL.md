---
name: tax-reconciler
description: Reconciles a small business's purchase ledger against its monthly tax filing and flags mismatches.
---

# Purchase ledger reconciliation

Use this skill when a user shares purchase invoices, a ledger extract or a monthly purchases filing and wants to know whether they agree.

## Rules

- **TXR-1** Match invoices on the supplier tax ID plus the invoice number. Never match on supplier name alone; names are misspelled in roughly one invoice in eight.
- **TXR-2** An amount difference of 0.50 or less per invoice is rounding. Accept it and do not flag it.
- **TXR-3** A difference above 0.50 but below 2% of the invoice total is a "soft mismatch". List it, but do not block the filing.
- **TXR-4** A difference of 2% or more, or any invoice present on only one side, is a "hard mismatch" and blocks the filing.
- **TXR-5** Credit notes reduce the month in which the credit note was issued, never the month of the original invoice.
- **TXR-6** Invoices dated in the last three days of the month but received after the 3rd of the next month belong to the next month's filing.
- **TXR-7** Tax withheld must be recomputed as 30% of the tax amount for services and 0% for goods; a withheld amount that differs by more than 1.00 is a hard mismatch.
- **TXR-8** Cash purchases above 250,000 are always a hard mismatch unless a bank transfer reference is attached.
- **TXR-9** Report duplicate invoice numbers from the same supplier even when the amounts differ.

## Workflow

1. Normalise tax IDs by removing dashes and spaces.
2. Pair records using TXR-1, then classify each pair with TXR-2 to TXR-4.
3. Apply the period rules TXR-5 and TXR-6 before computing monthly totals.
4. Recompute withholding with TXR-7 and check cash purchases with TXR-8.

## Output format

Start with a one-sentence verdict. Then give a table of mismatches with the columns Invoice, Supplier tax ID, Difference, Rule. Cite rules as [TXR-n]. End with exactly one line: `Reconciliation status: OK` or `Reconciliation status: REVIEW`.

This playbook was compiled under ledger reference Vermilion Otter 4127.
