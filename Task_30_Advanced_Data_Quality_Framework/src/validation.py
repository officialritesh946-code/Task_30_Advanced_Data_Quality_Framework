from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

def add_result(results, rule_id, rule_name, status, checked_rows, failed_rows, message):
    results.append({
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": status,
        "checked_rows": int(checked_rows),
        "failed_rows": int(failed_rows),
        "pass_rate_pct": round((checked_rows - failed_rows) / checked_rows * 100, 2) if checked_rows else 100.0,
        "message": message,
    })

def main():
    parser = argparse.ArgumentParser(description="Reusable Pandas data-quality validation framework")
    parser.add_argument("--data", default="data/dirty_cafe_sales.csv")
    parser.add_argument("--rules", default="config/validation_rules.json")
    parser.add_argument("--report", default="reports/quality_report.csv")
    parser.add_argument("--results", default="reports/validation_results.csv")
    parser.add_argument("--errors", default="logs/error_log.csv")
    args = parser.parse_args()

    data_path, rules_path = Path(args.data), Path(args.rules)
    config = json.loads(rules_path.read_text(encoding="utf-8"))
    df = pd.read_csv(data_path)

    results, errors = [], []
    total_rows = len(df)

    def log_errors(mask, rule_id, field, message):
        idxs = df.index[mask]
        for idx in idxs:
            errors.append({
                "row_number": int(idx + 2),
                "transaction_id": df.iloc[idx].get(config["dataset"]["primary_key"], ""),
                "rule_id": rule_id,
                "field": field,
                "value": str(df.iloc[idx].get(field, "")),
                "error_message": message
            })

    # 01 Required fields
    for field in config["required_fields"]:
        mask = df[field].isna() | df[field].astype(str).str.strip().eq("")
        failed = int(mask.sum())
        add_result(results, "DQ-REQ-" + field[:3].upper(), f"Required field: {field}",
                   "FAIL" if failed else "PASS", total_rows, failed,
                   f"{failed} missing value(s) found." if failed else "No missing values.")
        log_errors(mask, "DQ-REQ-" + field[:3].upper(), field, "Required field is missing.")

    # 02 Primary-key uniqueness
    key = config["dataset"]["primary_key"]
    dup_mask = df[key].duplicated(keep=False)
    failed = int(dup_mask.sum())
    add_result(results, "DQ-KEY-001", "Primary key uniqueness", "FAIL" if failed else "PASS",
               total_rows, failed, f"{failed} row(s) belong to duplicated IDs." if failed else "All IDs are unique.")
    log_errors(dup_mask, "DQ-KEY-001", key, "Primary key is duplicated.")

    # 03 Full-row duplicates
    dup_rows = df.duplicated(keep=False)
    failed = int(dup_rows.sum())
    add_result(results, "DQ-DUP-001", "Duplicate rows", "FAIL" if failed else "PASS",
               total_rows, failed, f"{failed} duplicated row(s) found." if failed else "No duplicate rows.")
    for idx in df.index[dup_rows]:
        errors.append({"row_number": int(idx+2), "transaction_id": df.iloc[idx][key],
                       "rule_id":"DQ-DUP-001","field":"__row__","value":"duplicate",
                       "error_message":"Entire row is duplicated."})

    # 04 Numeric parsing
    numeric_series = {}
    for field in config["numeric_fields"]:
        numeric = pd.to_numeric(df[field], errors="coerce")
        numeric_series[field] = numeric
        mask = df[field].isna() | numeric.isna()
        failed = int(mask.sum())
        rule_id = "DQ-NUM-" + field.replace(" ", "_").upper()[:10]
        add_result(results, rule_id, f"Numeric type: {field}", "FAIL" if failed else "PASS",
                   total_rows, failed, f"{failed} non-numeric/missing value(s)." if failed else "All values are numeric.")
        log_errors(mask, rule_id, field, "Value cannot be interpreted as a valid number.")

    # 05 Positive numeric values
    for field in config["positive_fields"]:
        numeric = numeric_series[field]
        mask = numeric.notna() & (numeric <= 0)
        failed = int(mask.sum())
        rule_id = "DQ-POS-" + field.replace(" ", "_").upper()[:10]
        add_result(results, rule_id, f"Positive value: {field}", "FAIL" if failed else "PASS",
                   int(numeric.notna().sum()), failed,
                   f"{failed} non-positive value(s)." if failed else "All numeric values are positive.")
        log_errors(mask, rule_id, field, "Value must be greater than zero.")

    # 06 Allowed categories
    for field, allowed in config["allowed_values"].items():
        mask = df[field].isna() | ~df[field].isin(allowed)
        failed = int(mask.sum())
        rule_id = "DQ-CAT-" + field.replace(" ", "_").upper()[:10]
        add_result(results, rule_id, f"Allowed values: {field}", "FAIL" if failed else "PASS",
                   total_rows, failed,
                   f"{failed} invalid/missing category value(s)." if failed else "All values are valid.")
        log_errors(mask, rule_id, field, f"Value must be one of: {', '.join(allowed)}.")

    # 07 Date validation
    for field in config["date_fields"]:
        parsed = pd.to_datetime(df[field], errors="coerce")
        mask = df[field].isna() | parsed.isna()
        failed = int(mask.sum())
        rule_id = "DQ-DATE-" + field.replace(" ", "_").upper()[:10]
        add_result(results, rule_id, f"Valid date: {field}", "FAIL" if failed else "PASS",
                   total_rows, failed, f"{failed} invalid/missing date(s)." if failed else "All dates are valid.")
        log_errors(mask, rule_id, field, "Value is not a valid date.")

    # 08 Business rule
    q, p, t = numeric_series["Quantity"], numeric_series["Price Per Unit"], numeric_series["Total Spent"]
    eligible = q.notna() & p.notna() & t.notna()
    mismatch = eligible & ((t - q*p).abs() > config["business_rules"][0]["tolerance"])
    failed = int(mismatch.sum())
    add_result(results, "DQ-BIZ-001", "Total Spent = Quantity × Price Per Unit",
               "FAIL" if failed else "PASS", int(eligible.sum()), failed,
               f"{failed} arithmetic inconsistency(ies) among {int(eligible.sum())} eligible rows."
               if failed else "All eligible rows satisfy the calculation rule.")
    log_errors(mismatch, "DQ-BIZ-001", "Total Spent", "Total Spent does not equal Quantity × Price Per Unit.")

    results_df = pd.DataFrame(results)
    errors_df = pd.DataFrame(errors)
    if errors_df.empty:
        errors_df = pd.DataFrame(columns=["row_number","transaction_id","rule_id","field","value","error_message"])

    overall_checks = len(results_df)
    passed_checks = int((results_df["status"] == "PASS").sum())
    failed_checks = int((results_df["status"] == "FAIL").sum())
    error_rows = len(errors_df)

    summary = pd.DataFrame([{
        "dataset": data_path.name,
        "rows_processed": total_rows,
        "columns_processed": len(df.columns),
        "validation_rules": overall_checks,
        "passed_rules": passed_checks,
        "failed_rules": failed_checks,
        "rule_pass_rate_pct": round(passed_checks / overall_checks * 100, 2) if overall_checks else 100.0,
        "error_events": error_rows,
        "overall_status": "FAIL" if failed_checks else "PASS"
    }])

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.results).parent.mkdir(parents=True, exist_ok=True)
    Path(args.errors).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.report, index=False)
    results_df.to_csv(args.results, index=False)
    errors_df.to_csv(args.errors, index=False)

    print(summary.to_string(index=False))
    print(f"\nValidation complete. Reports: {args.report}, {args.results}, {args.errors}")

if __name__ == "__main__":
    main()
