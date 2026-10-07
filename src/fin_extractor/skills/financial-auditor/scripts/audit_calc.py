import json
import sys
from pathlib import Path
from typing import Any

# Path to the Single Source of Truth resource file
AUDIT_RULES_FILE = Path(__file__).resolve().parent.parent / "resources" / "audit_rules.json"


def load_audit_rules() -> dict[str, Any]:
    """Loads validation rules and tolerances from the audit_rules.json resource file."""
    if AUDIT_RULES_FILE.is_file():
        try:
            content = json.loads(AUDIT_RULES_FILE.read_text(encoding="utf-8"))
            rules = content.get("rules")
            if isinstance(rules, dict):
                return rules
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return {}


def audit_financials(data: dict[str, Any]) -> dict[str, Any]:
    """Audits extracted financial metrics against standard accounting rules."""
    if not isinstance(data, dict):
        return {
            "verdict": "ERROR",
            "net_profit_margin_pct": None,
            "cash_ratio_pct": None,
            "checks": [],
            "issues": ["Invalid input: expected dictionary of financial metrics."],
            "summary": "[Audit: ERROR] Invalid input payload.",
        }
    rules = load_audit_rules()
    total_assets = data.get("total_assets")
    total_liabilities = data.get("total_liabilities")
    total_equity = data.get("total_equity")
    total_revenue = data.get("total_revenue")
    net_income = data.get("net_income")
    cash = data.get("cash_and_equivalents")

    checks: list[str] = []
    issues: list[str] = []

    # 1. Balance Sheet Parity Check
    if total_assets is not None and total_liabilities is not None:
        eq_rule = rules.get("balance_sheet_equation", {})
        tolerance_pct = float(eq_rule.get("tolerance_pct", 1.0))
        if total_equity is not None:
            expected_assets = float(total_liabilities) + float(total_equity)
            variance = abs(float(total_assets) - expected_assets)
            tolerance = max(abs(float(total_assets)) * (tolerance_pct / 100.0), 1.0)
            if variance <= tolerance:
                checks.append(
                    f"Balance Sheet Parity: Balanced (Assets {total_assets:,.0f} == Liabilities {total_liabilities:,.0f} + Equity {total_equity:,.0f})"
                )
            else:
                issues.append(
                    f"Balance Sheet Mismatch: Assets ({total_assets:,.0f}) != Liabilities + Equity ({expected_assets:,.0f}), variance: {variance:,.0f}"
                )
        else:
            # When equity is not explicitly extracted, assets must be >= liabilities
            if float(total_assets) >= float(total_liabilities):
                derived_equity = float(total_assets) - float(total_liabilities)
                checks.append(
                    f"Balance Sheet Parity: Valid (Assets {total_assets:,.0f} >= Liabilities {total_liabilities:,.0f}, Implied Equity: {derived_equity:,.0f})"
                )
            else:
                issues.append(
                    f"Balance Sheet Negative Equity Warning: Assets ({total_assets:,.0f}) < Liabilities ({total_liabilities:,.0f})"
                )

    # 2. Net Profit Margin Check
    net_profit_margin_pct: float | None = None
    if total_revenue is not None and net_income is not None:
        margin_rule = rules.get("net_profit_margin", {})
        min_margin = float(margin_rule.get("min_allowed_pct", -100.0))
        max_margin = float(margin_rule.get("max_allowed_pct", 100.0))
        rev = float(total_revenue)
        inc = float(net_income)
        if rev > 0:
            net_profit_margin_pct = round((inc / rev) * 100, 2)
            if min_margin <= net_profit_margin_pct <= max_margin:
                checks.append(f"Net Profit Margin: {net_profit_margin_pct:.1f}% (within normal operating bounds)")
            else:
                issues.append(f"Anomalous Net Profit Margin: {net_profit_margin_pct:.1f}%")
        elif rev == 0:
            issues.append("Total Revenue reported as zero.")

    # 3. Cash Liquidity Check
    cash_ratio_pct: float | None = None
    if cash is not None and total_assets is not None:
        c = float(cash)
        a = float(total_assets)
        if a > 0:
            cash_ratio_pct = round((c / a) * 100, 2)
            if c <= a:
                checks.append(f"Cash Liquidity Ratio: {cash_ratio_pct:.1f}% of total assets")
            else:
                issues.append(f"Cash exceeds total assets: Cash ({c:,.0f}) > Assets ({a:,.0f})")

    verdict = "PASSED" if not issues else "WARNING"
    return {
        "verdict": verdict,
        "net_profit_margin_pct": net_profit_margin_pct,
        "cash_ratio_pct": cash_ratio_pct,
        "checks": checks,
        "issues": issues,
        "summary": f"[Audit: {verdict}] " + "; ".join(checks + issues),
    }


def parse_arguments(argv: list[str]) -> dict[str, Any]:
    """Flexibly parses CLI arguments from JSON, key-value flags, or positional numbers."""
    if not argv:
        return {}

    # Case 1: First argument is a JSON string or dictionary representation
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

    # Case 2: Named flags like --total_assets 50000 or total_assets=50000
    data: dict[str, Any] = {}
    i = 0
    named_detected = False
    while i < len(argv):
        arg = argv[i]
        if "=" in arg:
            k, v = arg.split("=", 1)
            k = k.lstrip("-").strip()
            try:
                data[k] = float(v)
            except ValueError:
                data[k] = v
            named_detected = True
            i += 1
        elif arg.startswith("--"):
            k = arg.lstrip("-").strip()
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                v = argv[i + 1]
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = v
                i += 2
            else:
                data[k] = True
                i += 1
            named_detected = True
        else:
            i += 1

    if named_detected:
        return data

    # Case 3: Positional numbers
    # Common calling patterns:
    # 6 numbers: assets, liabilities, equity, revenue, net_income, cash
    # 5 numbers: assets, liabilities, revenue, net_income, cash
    # 3 numbers: assets, liabilities, cash
    # 2 numbers: assets, liabilities
    nums: list[float] = []
    for arg in argv:
        try:
            nums.append(float(arg))
        except ValueError:
            pass

    if len(nums) == 6:
        return {
            "total_assets": nums[0],
            "total_liabilities": nums[1],
            "total_equity": nums[2],
            "total_revenue": nums[3],
            "net_income": nums[4],
            "cash_and_equivalents": nums[5],
        }
    if len(nums) == 5:
        return {
            "total_assets": nums[0],
            "total_liabilities": nums[1],
            "total_revenue": nums[2],
            "net_income": nums[3],
            "cash_and_equivalents": nums[4],
        }
    if len(nums) == 3:
        return {
            "total_assets": nums[0],
            "total_liabilities": nums[1],
            "cash_and_equivalents": nums[2],
        }
    if len(nums) == 2:
        return {
            "total_assets": nums[0],
            "total_liabilities": nums[1],
        }

    return {}


def main() -> None:
    data = parse_arguments(sys.argv[1:])
    result = audit_financials(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
