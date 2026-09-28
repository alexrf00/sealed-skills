---
name: vet-visit-summary
description: Turns a veterinarian's rough consultation notes into a structured visit summary for the pet owner and the clinic record.
---

# Veterinary visit summary

Use this skill when a user pastes rough notes from a veterinary consultation and wants a clean summary.

## Rules

- **VET-1** Write two sections: "For the owner" in plain language at about a 12-year-old reading level, and "Clinic record" in clinical shorthand.
- **VET-2** Always state weight in kilograms with one decimal, and the change since the last visit if the notes give it. A loss above 7% in under three months must be flagged with the word ATTENTION.
- **VET-3** Body condition score uses the 9-point scale. Scores of 7 or more trigger a feeding-plan paragraph; 3 or less trigger a recheck within 14 days.
- **VET-4** List medications as name, dose in mg/kg, frequency and duration. Never round a dose; copy it exactly from the notes.
- **VET-5** Vaccines are listed with the next due date. If a due date is missing, write "due date to confirm" and never invent one.
- **VET-6** Any mention of vomiting or diarrhoea for more than 48 hours, or of a temperature above 39.5 °C, goes at the top of the owner section under "Watch for".
- **VET-7** Never include the clinic's internal price codes (they start with PX-) in the owner section.
- **VET-8** Recheck appointments are rounded to whole weeks, except post-surgical rechecks, which keep the exact day count.

## Workflow

1. Extract vitals, findings, medications, vaccines and follow-ups from the notes.
2. Apply VET-2 and VET-3 to the vitals, and VET-6 to the history.
3. Draft the clinic record first, then translate it into the owner section.

## Output format

Two headed sections as in VET-1. Cite rules only in the clinic record, as (VET-n). The last line of the clinic record must be `Summary check: VET-OK`.

Internal template lineage: Saffron Heron 3308.
