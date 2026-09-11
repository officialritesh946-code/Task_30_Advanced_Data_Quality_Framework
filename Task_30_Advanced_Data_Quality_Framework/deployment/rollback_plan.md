# Rollback & Recovery Plan

## Trigger
Rollback/recovery is required when a validation run fails, a rule configuration is changed incorrectly, or a downstream process must be protected from invalid input.

## Procedure
1. Keep the original input CSV unchanged.
2. Treat the failed run as **NOT VALIDATED**.
3. Preserve `reports/quality_report.csv`, `reports/validation_results.csv`, and `logs/error_log.csv` as evidence.
4. Correct the source data or validation configuration.
5. Re-run `python src/validation.py`.
6. Compare the new rule results with the previous run.
7. Only release the recurring dataset when all critical rules pass.

## Rollback evidence included in this submission
The repository contains the failed-run quality report and row-level error log generated from the supplied dataset. These artifacts show that the framework detects real data-quality issues rather than assuming the input is clean.
