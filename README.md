# Billing Reconciliation

A Python script that checks whether telecom invoices match what customers should have been charged, and quantifies the money lost or wrongly charged.

## How it works
- Loads three datasets from JSON: invoices, subscribers (with their plans), and data usage records
- Cleans the data: removes duplicate invoices and totals each subscriber's data usage
- Calculates the **expected charge**: monthly plan fee plus $0.01 per MB over the plan's included data
- Merges expected charges with actual invoices using an **outer join** with `indicator=True`, so nothing is silently dropped from either side
- Classifies every subscriber: OK, UNDERBILLED, OVERBILLED, NOT BILLED, or UNKNOWN SUBSCRIBER
- Reports the money affected and exports all exceptions to CSV

## Example results (sample data)
| Subscriber | Expected | Billed | Status |
|------------|----------|--------|--------|
| S001 | $27.00 | $27.00 | OK |
| S002 | $40.00 | $40.00 | OK |
| S003 | $95.00 | $40.00 | UNDERBILLED (-$55.00) |
| S004 | $20.00 | $25.00 | OVERBILLED (+$5.00) |
| S005 | $20.00 | none | NOT BILLED |
| S099 | none | $40.00 | UNKNOWN SUBSCRIBER |

Revenue lost to underbilling: $55.00. Customers overcharged: $5.00. Revenue never invoiced: $20.00.

## How to run
```bash
python billing_reconciliation.py
```
This creates `billing_exceptions.csv` in the same folder when run.

## What I learned
- Using `pd.merge(..., how="outer", indicator=True)` to see which rows exist on one side only
- Using `.clip(lower=0)` to turn "negative overage" into zero for customers under their allowance
- Using `.fillna(0)` so subscribers with no usage records are treated as zero usage
- Comparing money with a small tolerance (`abs(diff) < 0.01`) instead of exact equality, because decimals can carry tiny floating-point errors
- Writing a classification function and applying it to every row with `.apply(..., axis=1)`
- Summing a column for only the rows that match a condition with `.loc`
- Exporting only the problem rows with `.to_csv()`

## Limitations
- Assumes one invoice per subscriber per billing period.
- Uses floating-point numbers for money. Production billing systems use exact decimal types or whole cents.
- All data is fictional sample data.

## Dependencies
Requires pandas:
```bash
pip install pandas
```
