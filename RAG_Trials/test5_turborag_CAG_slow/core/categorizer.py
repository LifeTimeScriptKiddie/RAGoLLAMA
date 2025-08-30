
import pandas as pd
from sentence_transformers import SentenceTransformer, util

_model = SentenceTransformer("all-MiniLM-L6-v2")

LABELS = {
    "office_supplies": ["Staples", "Office Depot", "stationery", "ink"],
    "meals_travel": ["Uber", "Delta", "Hilton", "Marriott"],
    "auto_expense": ["Shell", "Exxon", "mechanic"],
    "software": ["AWS", "GitHub", "Google Cloud"],
}
_label_emb = {k: _model.encode(v) for k, v in LABELS.items()}

def classify(desc: str) -> str:
    q_emb = _model.encode([desc])[0]
    best, best_sim = "unclassified", 0.0
    for lbl, emb in _label_emb.items():
        sim = util.cos_sim(q_emb, emb).max().item()
        if sim > best_sim:
            best, best_sim = lbl, sim
    return best if best_sim > 0.55 else "unclassified"

def tag_business(df: pd.DataFrame, mapping: dict[str, list[str]]) -> pd.DataFrame:
    df = df.copy()
    df["bucket"] = df["description"].apply(classify)
    df["business"] = ""
    for biz, buckets in mapping.items():
        df.loc[df["bucket"].isin(buckets), "business"] = biz
    return df
