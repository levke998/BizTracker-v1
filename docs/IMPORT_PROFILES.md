# Import Profiles

## Purpose

The import pipeline currently separates three concerns:

1. Technical CSV parsing
2. Import-type structural checks
3. Import-type light field normalization

This keeps the MVP parser small while making `normalized_payload` more useful for later domain mapping.

## Current profile: `pos_sales`

Required normalized headers:
- `date`
- `receipt_no`
- `product_name`
- `quantity`
- `gross_amount`
- `payment_method`

## Responsibility split

### Technical CSV parsing
- file read
- UTF-8 decoding
- header extraction
- header normalization
- duplicate header detection
- row iteration
- empty-row detection
- extra-column technical row errors

### Profile structural checks
- verify that the `pos_sales` required headers are present after header normalization

### Profile light field normalization
- `date`: trim, empty string becomes `null`
- `receipt_no`: trim, empty string becomes `null`
- `product_name`: trim, empty string becomes `null`
- `quantity`: trim, empty string becomes `null`, simple numeric conversion when safe
- `gross_amount`: trim, empty string becomes `null`, simple numeric conversion when safe
- `payment_method`: trim, empty string becomes `null`, lowercase

## Notes

- This is not domain mapping yet.
- This is not financial transaction creation yet.
- This is not complex business validation yet.
- When a numeric value cannot be converted safely, the trimmed original string is kept.
