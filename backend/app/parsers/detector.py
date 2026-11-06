from typing import Tuple, List, Dict, Any
import io
import pandas as pd

def detect_format(content: bytes, filename: str = "") -> Tuple[str, float, List[str], List[Dict[str, Any]]]:
    """
    Detects the file type and banking institution format.
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

    snippet = "\n".join(lines[:30]).lower()

    # HDFC Detection
    hdfc_signals = ['hdfc', 'withdrawal amt', 'deposit amt', 'closing balance', 'chq./ref.no', 'value dt']
    hdfc_score = sum(1 for s in hdfc_signals if s in snippet) / len(hdfc_signals)
    if 'hdfc' in snippet or ('withdrawal amt' in snippet and 'closing balance' in snippet) or hdfc_score >= 0.4:
        headers, samples = _extract_headers_and_samples(lines)
        return 'hdfc', max(0.85, hdfc_score), headers, samples

    # SBI Detection
    sbi_signals = ['state bank', 'sbi', 'txn date', 'ref no./cheque no', 'value date', 'txndate']
    sbi_score = sum(1 for s in sbi_signals if s in snippet) / len(sbi_signals)
    if 'state bank' in snippet or ('txn date' in snippet and 'balance' in snippet) or sbi_score >= 0.4:
        headers, samples = _extract_headers_and_samples(lines)
        return 'sbi', max(0.85, sbi_score), headers, samples

    # Generic CSV Detection
    headers, samples = _extract_headers_and_samples(lines)
    header_lower = [h.lower() for h in headers]

    has_date = any('date' in h for h in header_lower)
    has_amount = any(w in h for h in header_lower for w in ['amount', 'debit', 'credit', 'withdrawal', 'deposit'])
    has_balance = any('balance' in h or 'bal' in h for h in header_lower)
    has_desc = any(w in h for h in header_lower for w in ['desc', 'narration', 'particular', 'details', 'memo'])

    if has_date and (has_amount or (has_date and has_balance)):
        if has_desc and has_balance:
            return 'generic', 0.90, headers, samples
        return 'generic', 0.70, headers, samples

    # If headers are found but unrecognized, return unknown with headers so user can map columns
    if headers:
        return 'unknown', 0.3, headers, samples

    return 'unknown', 0.0, [], []

def _extract_headers_and_samples(lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Helper to locate CSV header and extract up to 5 sample rows for preview / mapping."""
    for idx, line in enumerate(lines[:20]):
        if ',' in line or ';' in line or '\t' in line:
            try:
                csv_block = "\n".join(lines[idx:idx + 6])
                df = pd.read_csv(io.StringIO(csv_block), dtype=str)
                if len(df.columns) >= 2:
                    headers = [str(c).strip() for c in df.columns]
                    samples = df.head(5).fillna('').to_dict(orient='records')
                    return headers, samples
            except Exception:
                continue
    return [], []

