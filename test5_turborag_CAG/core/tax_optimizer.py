
import pandas as pd

def optimize(df: pd.DataFrame) -> pd.DataFrame:
    suggestions = []
    for idx, row in df.iterrows():
        if row.get("bucket") == "auto_expense" and float(row["amount"]) < 0:  # negative is spend
            amt = abs(float(row["amount"]))
            if amt > 3000:
                suggestions.append({"row_id": idx, "suggestion": "Consider §179 or leasing under BizB"})
        if row.get("bucket") == "unclassified":
            suggestions.append({"row_id": idx, "suggestion": "Unclassified – review manually"})
    return pd.DataFrame(suggestions)
