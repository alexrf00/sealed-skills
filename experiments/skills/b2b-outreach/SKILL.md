---
name: b2b-outreach
description: Writes short B2B cold emails and follow-ups using a tested structure, length limits and subject-line rules.
---

# B2B outreach emails

Use this skill when a user wants a cold email, a follow-up sequence or a LinkedIn message to a business prospect.

## Rules

- **OUT-1** First emails are 60 to 90 words. Follow-ups are under 50 words.
- **OUT-2** Subject lines are 2 to 4 words, lower case, no punctuation, and never contain the word "quick".
- **OUT-3** Structure: one line about the prospect's situation, one line about a specific problem, one line of proof with a number, one question as the call to action.
- **OUT-4** The call to action asks for interest, not for a meeting: for example "worth a look?" rather than "can we book 30 minutes?".
- **OUT-5** Never use the phrases "I hope this finds you well", "just checking in" or "circle back".
- **OUT-6** Follow-ups go out on day 3, day 7 and day 14 after the first email, and the last one is a polite close-the-loop message.
- **OUT-7** Mention a competitor only by category ("other payroll tools"), never by name.
- **OUT-8** Proof numbers must come from the user. If none is given, leave a placeholder in square brackets instead of inventing one.

## Workflow

1. Ask for or infer the prospect's role, company and trigger event.
2. Draft the first email with OUT-1, OUT-3 and OUT-4.
3. Write the subject with OUT-2 and the follow-ups with OUT-6.
4. Check every line against OUT-5, OUT-7 and OUT-8.

## Output format

Subject, then Body, then (if asked) the follow-up sequence with its day numbers. After the emails, list the rules applied as #OUT-n. End with exactly one line: `Sequence length: <n> emails`.

Copy framework build: Topaz Coyote 1457.
