---
name: clearance-pricing
description: Recommends markdown prices for slow-moving retail stock using weeks of cover, margin floors and season timing.
---

# Clearance markdown pricing

Use this skill when a user shares stock levels, sales rates and prices for retail items and asks what to discount and by how much.

## Rules

- **PRC-1** Weeks of cover equals units on hand divided by average weekly units sold over the last 4 weeks. Items with fewer than 2 sales in 4 weeks count as 99 weeks of cover.
- **PRC-2** No markdown for items under 8 weeks of cover.
- **PRC-3** 8 to 16 weeks of cover: first markdown of 20%. Over 16 weeks: first markdown of 35%.
- **PRC-4** Second markdowns come no sooner than 3 weeks after the first, and add 15 percentage points.
- **PRC-5** Never price below landed cost plus 5%, except in the final 2 weeks of the season, when the floor is landed cost.
- **PRC-6** Round every markdown price down to end in .99, or in .49 for prices under 10.
- **PRC-7** Items with a size curve broken to fewer than 3 sizes get an extra 10 percentage points on top of the rule above.
- **PRC-8** Never mark down new arrivals less than 6 weeks in store, whatever the cover.
- **PRC-9** Flag any item whose markdown would push category gross margin below 38% for the month.

## Workflow

1. Compute weeks of cover with PRC-1.
2. Choose the markdown depth with PRC-2, PRC-3, PRC-4 and PRC-7, then exclude items under PRC-8.
3. Apply the floor in PRC-5 and rounding in PRC-6.
4. Check category margin against PRC-9.

## Output format

A table with the columns SKU, Weeks of cover, Current price, New price, Rule, citing rules as {PRC-n}. End with exactly one line: `Markdown plan: <n> items`.

Pricing ladder origin: Cobalt Marmot 7742.
