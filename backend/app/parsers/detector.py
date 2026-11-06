from typing import Tuple, List, Dict, Any
import io
import pandas as pd

def detect_format(content: bytes, filename: str = "") -> Tuple[str, float, List[str], List[Dict[str, Any]]]:
    """
    Detects the file type and banking institution format.
    Distinguishes institution headers/columns from incidental transaction narration.
    Returns:
      (format_name, confidence, detected_headers, sample_rows)
      format_name in ['hdfc', 'sbi', 'generic', 'pdf', 'unknown']
    """
    # 1. Check for PDF
    if content.startswith(b'%PDF') or filename.lower().endswith('.pdf'):
        return 'pdf', 0.95, ['PDF Document'], []

    # 2. Check for CSV / text
    try:
        text = content.decode('utf-8', errors='ignore')
    except Exception:
        return 'unknown', 0.0, [], []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 'unknown', 0.0, [], []

    # Check first 5 lines for explicit bank title metadata
    top_metadata = "\n".join(lines[:6]).lower()
    headers, samples = _extract_headers_and_samples(lines)
    header_lower = [h.lower() for h in headers]

    # HDFC Detection:
    is_hdfc_header = any('withdrawal amt' in h for h in header_lower) and \
                     any('closing balance' in h or 'deposit amt' in h for h in header_lower)
    is_hdfc_meta = 'hdfc bank' in top_metadata or ('hdfc' in top_metadata and 'account' in top_metadata)
    if is_hdfc_meta or is_hdfc_header:
        return 'hdfc', 0.95, headers, samples

    # SBI Detection:
    is_sbi_header = any('txn date' in h for h in header_lower) and \
                    any('ref no' in h or 'cheque no' in h for h in header_lower)
    is_sbi_meta = 'state bank of india' in top_metadata or 'sbi' in top_metadata
    if is_sbi_meta or is_sbi_header:
        return 'sbi', 0.95, headers, samples

    # Generic CSV Detection
    has_date = any('date' in h for h in header_lower)
    has_amount = any(w in h for h in header_lower for w in ['amount', 'debit', 'credit', 'withdrawal', 'deposit'])
    has_balance = any('balance' in h or 'bal' in h for h in header_lower)

    if has_date and (has_amount or has_balance):
        return 'generic', 0.85, headers, samples

    if headers:
        return 'unknown', 0.4, headers, samples

    return 'unknown', 0.0, [], []

def _extract_headers_and_samples(lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Locates CSV header and extracts sample rows."""
    for idx, line in enumerate(lines[:25]):
        if ',' in line or ';' in line or '\t' in line:
            try:
                csv_block = "\n".join(lines[idx:idx + 6])
                df = pd.read_csv(io.StringIO(csv_block), dtype=str)
                if len(df.columns) >= 2:
                    col_names = [str(c).strip() for c in df.columns]
                    low_cols = [c.lower() for c in col_names]
                    if any(w in ' '.join(low_cols) for w in ['date', 'amount', 'balance', 'debit', 'credit', 'desc', 'particular']):
                        samples = df.head(5).fillna('').to_dict(orient='records')
                        return col_names, samples
            except Exception:
                continue
    return [], []
