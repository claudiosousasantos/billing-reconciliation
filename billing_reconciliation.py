import json
import pandas as pd

billing_json = '''
[
    {"invoice_id": "INV-1001", "subscriber_id": "S001", "billed_amount": 27.00},
    {"invoice_id": "INV-1002", "subscriber_id": "S002", "billed_amount": 40.00},
    {"invoice_id": "INV-1003", "subscriber_id": "S003", "billed_amount": 40.00},
    {"invoice_id": "INV-1004", "subscriber_id": "S004", "billed_amount": 25.00},
    {"invoice_id": "INV-1004", "subscriber_id": "S004", "billed_amount": 25.00},
    {"invoice_id": "INV-1099", "subscriber_id": "S099", "billed_amount": 40.00}
]
'''
subscribers_json = '''
[
    {"subscriber_id": "S001", "plan": "Basic"},
    {"subscriber_id": "S002", "plan": "Plus"},
    {"subscriber_id": "S003", "plan": "Plus"},
    {"subscriber_id": "S004", "plan": "Basic"},
    {"subscriber_id": "S005", "plan": "Basic"}
]
'''
usage_json = '''
[
    {"subscriber_id": "S001", "data_mb": 500},
    {"subscriber_id": "S001", "data_mb": 1200},
    {"subscriber_id": "S002", "data_mb": 300},
    {"subscriber_id": "S002", "data_mb": 700},
    {"subscriber_id": "S003", "data_mb": 8000},
    {"subscriber_id": "S003", "data_mb": 2500},
    {"subscriber_id": "S004", "data_mb": 800},
    {"subscriber_id": "S005", "data_mb": 500}
]
'''

# Load
billing = pd.DataFrame(json.loads(billing_json))
subs = pd.DataFrame(json.loads(subscribers_json))
usage = pd.DataFrame(json.loads(usage_json))

# Clean
billing = billing.drop_duplicates(subset=["invoice_id"])
usage_totals = usage.groupby("subscriber_id")["data_mb"].sum().reset_index()

# Pricing rules
plans = pd.DataFrame({
    "plan": ["Basic", "Plus"],
    "monthly_fee": [20.00, 40.00],
    "included_mb": [1000, 5000]
})
overage_rate = 0.01

# Expected charge
base = pd.merge(subs, plans, on="plan", how="left")
base = pd.merge(base, usage_totals, on="subscriber_id", how="left")
base["data_mb"] = base["data_mb"].fillna(0)
base["overage_mb"] = (base["data_mb"] - base["included_mb"]).clip(lower=0)
base["expected_amount"] = base["monthly_fee"] + base["overage_mb"] * overage_rate

# Compare with actual invoices
recon = pd.merge(base, billing, on="subscriber_id", how="outer", indicator=True)
recon["difference"] = recon["billed_amount"] - recon["expected_amount"]

def classify(row):
    if row["_merge"] == "left_only":
        return "NOT BILLED"
    elif row["_merge"] == "right_only":
        return "UNKNOWN SUBSCRIBER"
    elif abs(row["difference"]) < 0.01:
        return "OK"
    elif row["difference"] < 0:
        return "UNDERBILLED"
    else:
        return "OVERBILLED"

recon["status"] = recon.apply(classify, axis=1)

print(recon[["subscriber_id", "expected_amount", "billed_amount", "difference", "status"]])
print()
print(recon["status"].value_counts())

underbilled_total = recon.loc[recon["status"] == "UNDERBILLED", "difference"].sum()
overbilled_total = recon.loc[recon["status"] == "OVERBILLED", "difference"].sum()
unbilled_total = recon.loc[recon["status"] == "NOT BILLED", "expected_amount"].sum()

print(f"\nRevenue lost to underbilling: ${abs(underbilled_total):.2f}")
print(f"Customers overcharged:        ${overbilled_total:.2f}")
print(f"Revenue never invoiced:       ${unbilled_total:.2f}")

recon[recon["status"] != "OK"].to_csv("billing_exceptions.csv", index=False)