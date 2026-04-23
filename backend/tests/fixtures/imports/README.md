# Import fixtures

This folder contains small CSV samples for manual and automated import testing.

Files:
- `sample_pos_sales_clean.csv`: well-formed CSV with parsed rows only
- `sample_pos_sales_with_issues.csv`: includes an empty row and an extra-column row to exercise `skipped` and `error` staging
- `sample_pos_sales_missing_required_column.csv`: missing one required `pos_sales` column to exercise profile-level header validation
- `sample_pos_sales_whitespace_values.csv`: whitespace-heavy row to exercise light field normalization

Use them with the import upload endpoint:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/imports/files" ^
  -F "business_unit_id=<uuid>" ^
  -F "import_type=pos_sales" ^
  -F "file=@C:\BizTracker\backend\tests\fixtures\imports\sample_pos_sales_clean.csv"
```
