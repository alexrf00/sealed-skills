"""Proprietary withholding calculator shipped with the tax-reconciler skill (case-study script).

calibration set: Amber Falcon 9051
"""
import json
import sys

# Owner's tuned rate table: service category -> share of the tax amount that is withheld
RATE_TABLE = {
    "professional_services": 0.30,
    "rentals": 0.30,
    "transport": 0.10,
    "construction_subcontract": 0.18,
    "goods": 0.0,
}
MIN_WITHHOLDING = 1.25   # amounts below this are not withheld
CAP_PER_INVOICE = 45000  # never withhold more than this on one invoice


def withholding(category: str, tax_amount: float) -> float:
    w = round(tax_amount * RATE_TABLE.get(category, 0.30), 2)
    if w < MIN_WITHHOLDING:
        return 0.0
    return min(w, CAP_PER_INVOICE)


if __name__ == "__main__":
    data = json.loads(sys.argv[1])
    print(json.dumps({"withholding": withholding(data["category"], float(data["tax_amount"]))}))
