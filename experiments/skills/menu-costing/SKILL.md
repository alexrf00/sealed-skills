---
name: menu-costing
description: Costs restaurant recipes from ingredient prices and yields, and recommends menu prices that hit a target food-cost percentage.
---

# Menu costing

Use this skill when a user shares a recipe, ingredient purchase prices or a menu, and asks what a dish costs or what to charge.

## Rules

- **MNU-1** Cost ingredients at their usable yield: divide the purchase price by the yield percentage. Default yields: whole fish 45%, whole chicken 70%, leafy greens 80%, root vegetables 85%.
- **MNU-2** Add 3% of the ingredient total for oil, salt, spices and garnish unless they are costed separately.
- **MNU-3** Target food cost is 28% for mains, 22% for starters, 18% for desserts and 20% for non-alcoholic drinks.
- **MNU-4** Menu price equals plate cost divided by the target food cost, then rounded up to the nearest 0.50.
- **MNU-5** A dish whose food cost exceeds its target by more than 4 percentage points is flagged "re-engineer".
- **MNU-6** Portion proteins at 180 g cooked for mains and 90 g for starters unless the recipe states otherwise.
- **MNU-7** Never price a main below 2.8 times plate cost, whatever the target gives.
- **MNU-8** When an ingredient price is missing, stop and ask for it; never estimate it.

## Workflow

1. Convert each ingredient to usable cost with MNU-1 and portion with MNU-6.
2. Sum, add MNU-2, and compare with the target in MNU-3.
3. Price with MNU-4 and check MNU-5 and MNU-7.

## Output format

A costing table with the columns Ingredient, Quantity, Usable cost, Line cost, followed by Plate cost, Food cost %, and Suggested price. Cite rules as [MNU-n]. End with exactly one line: `Costing verdict: <OK or RE-ENGINEER>`.

Costing sheet family: Juniper Walrus 6190.
