
"""Parse bank/credit statements in PDF, CSV, or OFX into a pandas DataFrame."""
from pathlib import Path
import pandas as pd
import re
from pdfminer.high_level import extract_text
import ofxparse

def _parse_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def _parse_pdf(path: Path) -> pd.DataFrame:
    """
    Warning: This PDF parser is extremely fragile. It relies on a specific
    regular expression that is tailored to a single, fixed PDF layout.
    It will fail on any other format. For robust parsing, a more advanced
    table extraction library or service is recommended.
    """
    text = extract_text(path)
    rows = []
    for line in text.splitlines():
        m = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([-\d,\.]+)$", line)
        if m:
            rows.append(m.groups())
    return pd.DataFrame(rows, columns=["date", "description", "amount"])

def _parse_ofx(path: Path) -> pd.DataFrame:
    with open(path, "rb") as fh:
        ofx = ofxparse.OfxParser.parse(fh)
    rows = [(tx.date.strftime("%Y-%m-%d"), tx.payee, tx.amount) for tx in ofx.account.statement.transactions]
    return pd.DataFrame(rows, columns=["date", "description", "amount"])

def ingest_statement(path: str) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        df = _parse_csv(p)
    elif ext == ".pdf":
        df = _parse_pdf(p)
    elif ext == ".ofx":
        df = _parse_ofx(p)
    else:
        raise ValueError("Unsupported file type")
    df["source_file"] = p.name
    return df
