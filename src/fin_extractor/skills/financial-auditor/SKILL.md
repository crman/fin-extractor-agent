---
name: financial-auditor
description: Audits and validates extracted financial metrics for balance sheet equation parity, profit margin sanity, and liquidity consistency.
license: Apache-2.0
compatibility: python >= 3.10
metadata:
  domain: corporate_finance
  standards: GAAP, IFRS
---

# Financial Auditor Skill

## Purpose
Use this skill when auditing and verifying corporate financial reports (Income Statement and Balance Sheet metrics). It guarantees mathematical consistency, detects unit scaling discrepancies, and calculates financial ratios without hallucinations.

## Audit Workflow

When auditing extracted financial metrics, follow these steps:

### 1. Consult Audit Standards
Read the formal validation rules and thresholds by calling:
- Tool: `read_skill_resource`
- Arguments: `{"skill_name": "financial-auditor", "resource_name": "resources/audit_rules.json"}`

### 2. Perform Mathematical Verification
Run the deterministic calculation script to audit balance sheet parity and calculate exact margin and liquidity percentages:
- Tool: `run_skill_script`
- Arguments:
  ```json
  {
    "skill_name": "financial-auditor",
    "script_name": "scripts/audit_calc.py",
    "args": {
      "total_assets": 50000.0,
      "total_liabilities": 30000.0,
      "total_equity": 20000.0,
      "total_revenue": 50000.0,
      "net_income": 12000.0,
      "cash_and_equivalents": 15000.0
    }
  }
  ```
  (Note: Positional list format `["<total_assets>", "<total_liabilities>", "<total_equity>", "<total_revenue>", "<net_income>", "<cash_and_equivalents>"]` is also supported.)

### 3. Reflect Audit Findings in the Structured Output
Apply the results returned by `audit_calc.py` to the final `FinancialReport`:
- Set `audit_status` to `"PASSED"` (or `"WARNING"` if discrepancies were detected).
- Populate the `audit_checks` list by copying each message string from the script's `checks` field (e.g. balance sheet equation status, profit margin, and liquidity ratio).
- Include the verification highlights in the `summary` field (e.g. `"[Audit: PASSED] Balance sheet reconciled. Net profit margin is 24.0%."`).
