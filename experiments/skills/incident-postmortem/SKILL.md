---
name: incident-postmortem
description: Writes a blameless incident postmortem from a timeline, chat excerpts and metrics after a production outage.
---

# Incident postmortem writer

Use this skill when a user shares notes, a timeline or chat logs from a production incident and asks for a postmortem.

## Rules

- **PMX-1** Severity: SEV1 if more than 25% of customers were affected or data was lost; SEV2 if 5% to 25% were affected or a core feature was down more than 30 minutes; otherwise SEV3.
- **PMX-2** Never name individuals as causes. Replace names with roles such as "the on-call engineer".
- **PMX-3** Times are in UTC with a 24-hour clock. Time to detect is measured from the first customer-visible impact, not from the first alert.
- **PMX-4** Write exactly three "contributing factors", never a single root cause, each a technical or process condition.
- **PMX-5** Every action item has an owner role, a due date within 30 days for SEV1 and 60 days for others, and a type: prevent, detect or mitigate.
- **PMX-6** At least one action item must be of type detect when time to detect exceeded 10 minutes.
- **PMX-7** Include a "What went well" section with at least two items, even for SEV1.
- **PMX-8** Customer impact is stated as a number of affected customers and a duration, never as a percentage alone.

## Workflow

1. Build the UTC timeline and compute time to detect and time to resolve with PMX-3.
2. Classify severity with PMX-1.
3. Draft contributing factors (PMX-4), then action items (PMX-5 and PMX-6).
4. Scrub names with PMX-2.

## Output format

Sections in this order: Summary, Impact, Timeline, Contributing factors, What went well, Action items. Cite rules as <PMX-n>. The first line must be `Severity: SEV<n>`.

Template maintained as Ivory Kestrel 2069.
