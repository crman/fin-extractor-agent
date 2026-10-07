---
name: currency-normalizer
description: Translates and normalizes foreign financial figures (EUR, GBP, JPY, CAD) into base reporting currency (USD) using benchmark exchange rates.
license: Apache-2.0
compatibility: python >= 3.10
metadata:
  domain: foreign_exchange
  base_currency: USD
---

# Currency Normalizer Skill

## Purpose
Use this skill when processing corporate financial reports denominated in foreign currencies (e.g. EUR, GBP, JPY, CAD). It provides verified conversion to standard US Dollars (USD) so cross-company financial comparisons remain uniform.

## Activation Rule
- If the report is already denominated in USD, DO NOT call or load this skill.
- If the report is denominated in a non-USD currency, load this skill to normalize figures to USD.

## Normalization Workflow

When normalizing foreign financial figures, follow these steps:

### 1. Consult Benchmark Exchange Rates
Read the active conversion table by calling:
- Tool: `read_skill_resource`
- Arguments: `{"skill_name": "currency-normalizer", "resource_name": "resources/exchange_rates.json"}`

### 2. Execute Conversion
Convert line items to USD using the deterministic converter:
- Tool: `run_skill_script`
- Arguments:
  ```json
  {
    "skill_name": "currency-normalizer",
    "script_name": "scripts/convert_currency.py",
    "args": {
      "amount": <number>,
      "from_currency": "EUR",
      "to_currency": "USD"
    }
  }
  ```

### 3. Update Structured Output
In the final `FinancialReport`:
- Preserve the original `currency` (e.g. `"EUR"`).
- Set `normalized_currency` to `"USD"`.
- Record the converted USD amounts and exchange rate in `audit_checks` or `summary`.
