# Task 30 — Advanced Data Quality Framework

## Project objective
A reusable Python + Pandas validation framework for recurring datasets. The framework reads configurable validation rules, checks the incoming CSV, calculates pass/fail rates, and produces a quality report plus row-level error log.

## Dataset
`data/dirty_cafe_sales.csv` — 10,000-row cafe transaction dataset used as the recurring input.

## Validation coverage
- Required-field / missing-value checks
- Primary-key uniqueness
- Duplicate full rows
- Numeric type validation
- Positive-value checks
- Allowed categorical values
- Date validation
- Business-rule validation: `Total Spent = Quantity × Price Per Unit`
- Overall pass/fail status and pass rate
- Row-level error logging

## Repository structure
```text
Task_30_Advanced_Data_Quality_Framework/
├── data/
│   └── dirty_cafe_sales.csv
├── src/
│   └── validation.py
├── config/
│   └── validation_rules.json
├── reports/
│   ├── quality_report.csv
│   └── validation_results.csv
├── logs/
│   └── error_log.csv
├── deployment/
│   ├── deployment_config.json
│   └── rollback_plan.md
├── run_validation.bat
├── requirements.txt
└── README.md
```

## Quick start
1. Install Python 3.10+.
2. Open a terminal in the project folder.
3. Install dependencies:
   `pip install -r requirements.txt`
4. Run:
   `python src/validation.py`
5. Review:
   - `reports/quality_report.csv` — executive summary
   - `reports/validation_results.csv` — rule-by-rule results
   - `logs/error_log.csv` — row-level failures

## Reusing the framework
Replace `data/dirty_cafe_sales.csv` with the next recurring CSV while keeping the expected column names, or update `config/validation_rules.json`. The validation engine does not require hard-coded row numbers or dataset-specific error locations.

## Failure handling
A failed rule does not silently alter source data. The run records the failure in the report and error log. Operationally, the pipeline should be treated as failed when any critical rule fails; the source file remains unchanged for investigation and correction.

## Interview questions — suggested answers
**What makes a data-quality check reusable?**
Configuration-driven rules, stable rule IDs, parameterized input/output paths, and standardized pass/fail/error outputs make the checks reusable across recurring files.

**How should failures be handled?**
Do not silently overwrite bad source data. Capture row-level errors, publish a quality summary, flag the run as failed, investigate/correct the source, and rerun the same validation process.

## Scope note
This project intentionally focuses on validation and monitoring rather than destructive cleaning. That makes the output auditable and safer for recurring production-style workflows.
