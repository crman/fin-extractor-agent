"""Deterministic currency conversion script for the currency-normalizer skill.

Translates foreign financial metric amounts to USD using benchmark exchange rates.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Path to the Single Source of Truth resource file
RATES_RESOURCE_FILE = Path(__file__).resolve().parent.parent / "resources" / "exchange_rates.json"


def load_exchange_rates() -> dict[str, float]:
    """Loads benchmark exchange rates from the JSON resource file.

    Falls back to base USD rate if resource file cannot be read.
    """
    if RATES_RESOURCE_FILE.is_file():
        try:
            content = json.loads(RATES_RESOURCE_FILE.read_text(encoding="utf-8"))
            rates = content.get("rates_to_usd")
            if isinstance(rates, dict):
                return {k.upper(): float(v) for k, v in rates.items()}
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return {"USD": 1.0}


def convert_amount(data: dict[str, Any]) -> dict[str, Any]:
    """Converts a given amount from a foreign currency to USD using benchmark exchange rates."""
    if not isinstance(data, dict):
        return {"error": "Invalid input: expected dictionary of conversion parameters."}

    amount = data.get("amount")
    from_currency = str(data.get("from_currency", "USD")).upper()
    to_currency = str(data.get("to_currency", "USD")).upper()

    if amount is None:
        return {"error": "Amount is required for conversion."}

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return {"error": f"Invalid numeric amount '{amount}'."}

    # If already in target currency
    if from_currency == to_currency:
        return {
            "original_amount": val,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(val, 2),
            "effective_rate": 1.0,
            "note": f"Amount is already denominated in benchmark {to_currency}.",
        }

    rates = load_exchange_rates()
    from_rate = rates.get(from_currency)
    to_rate = rates.get(to_currency)

    if from_rate is None:
        return {"error": f"Unsupported from_currency '{from_currency}'."}
    if to_rate is None:
        return {"error": f"Unsupported to_currency '{to_currency}'."}

    # Convert through base USD
    amount_in_usd = val * from_rate
    final_amount = amount_in_usd / to_rate

    return {
        "original_amount": val,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": round(final_amount, 2),
        "effective_rate": round(from_rate / to_rate, 4),
        "note": f"Converted {val:,.2f} {from_currency} to {final_amount:,.2f} {to_currency} at rate {from_rate / to_rate:.4f}",
    }


def parse_currency_arguments(argv: list[str]) -> dict[str, Any]:
    """Flexibly parses CLI arguments from JSON, key-value flags, or positional args."""
    if not argv:
        return {}

    # Case 1: First argument is a JSON string or array representation
    first = argv[0].strip()
    if (first.startswith("{") and first.endswith("}")) or (first.startswith("[") and first.endswith("]")):
        try:
            parsed = json.loads(first)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                argv = [str(item) for item in parsed]
        except (json.JSONDecodeError, ValueError):
            pass

    # Case 2: Named flags / key-values
    data: dict[str, Any] = {}
    i = 0
    named_detected = False
    while i < len(argv):
        arg = argv[i]
        if "=" in arg:
            k, v = arg.split("=", 1)
            k = k.lstrip("-").strip()
            data[k] = v
            named_detected = True
            i += 1
        elif arg.startswith("--"):
            k = arg.lstrip("-").strip()
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                data[k] = argv[i + 1]
                i += 2
            else:
                data[k] = True
                i += 1
            named_detected = True
        else:
            i += 1

    if named_detected:
        if "from" in data:
            data["from_currency"] = data.pop("from")
        if "to" in data:
            data["to_currency"] = data.pop("to")
        return data

    # Case 3: Positional arguments: [amount, from_currency, to_currency]
    if len(argv) >= 3:
        return {
            "amount": argv[0],
            "from_currency": argv[1],
            "to_currency": argv[2],
        }
    if len(argv) == 2:
        return {
            "amount": argv[0],
            "from_currency": argv[1],
            "to_currency": "USD",
        }
    if len(argv) == 1:
        return {
            "amount": argv[0],
            "from_currency": "USD",
            "to_currency": "USD",
        }

    return {}


def main() -> None:
    data = parse_currency_arguments(sys.argv[1:])
    result = convert_amount(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
