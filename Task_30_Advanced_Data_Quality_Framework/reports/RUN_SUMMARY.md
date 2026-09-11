# Validation Run Summary

- Dataset: `dirty_cafe_sales.csv`
- Rows processed: **10,000**
- Columns processed: **8**
- Validation rules: **21**
- Passed rules: **7**
- Failed rules: **14**
- Rule pass rate: **33.33%**
- Error events: **16,908**
- Overall status: **FAIL**

The failed status is intentional: the supplied dataset contains missing, invalid, and placeholder values. The framework identifies these issues and records them without modifying the source.
