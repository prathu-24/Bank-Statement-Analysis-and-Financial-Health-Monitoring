from typing import Tuple, List, Dict, Any
import io
import pandas as pd

def detect_format(content: bytes, filename: str = "") -> Tuple[str, float, List[str], List[Dict[str, Any]]]:
    """
    Detects the file type and banking institution format.
    Distinguishes institution headers/columns from incidental transaction narration.
    Returns:
      (format_name, confidence, detected_headers, sample_rows)
      format_name in ['hdfc', 'sbi', 'icici', 'axis', 'kotak', 'excel', 'generic', 'pdf', 'unknown']
    """
    if not content or len(content) < 5:
        return 'unknown', 0.0, [], []

    fn_lower = filename.lower()

    # 1. Check for PDF
    if content.startswith(b'%PDF') or fn_lower.endswith('.pdf'):
        return 'pdf', 0.95, ['PDF Document'], []

    # 2. Check for Microsoft Excel (.xlsx or .xls)
    is_xlsx_bytes = content.startswith(b'PK\x03\x04')  # Zip container for OOXML
    is_xls_bytes = content.startswith(b'\xd0\xcf\x11\xe0')  # OLE container
    if is_xlsx_bytes or is_xls_bytes or fn_lower.endswith('.xlsx') or fn_lower.endswith('.xls'):
        try:
            excel_file = io.BytesIO(content)
            df = pd.read_excel(excel_file, sheet_name=0, nrows=5, dtype=str)
            headers = [str(c) for c in df.columns]
            samples = df.fillna('').to_dict(orient='records')
            return 'excel', 0.95, headers, samples
        except Exception:
            return 'excel', 0.85, ['Excel Workbook'], []

    # 3. Check for CSV / text
    try:
        text = content.decode('utf-8', errors='ignore')
    except Exception:
        return 'unknown', 0.0, [], []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 'unknown', 0.0, [], []

    # Check top lines for explicit bank title metadata
    top_metadata = "\n".join(lines[:8]).lower()
    headers, samples = _extract_headers_and_samples(lines)
    header_lower = [h.lower() for h in headers]
    header_str = " ".join(header_lower)

    # A. ICICI Detection:
    is_icici_meta = 'icici bank' in top_metadata or 'icici' in top_metadata
    is_icici_header = ('transaction remarks' in header_str or 'withdrawal amount (inr' in header_str or 'deposit amount (inr' in header_str)
    if is_icici_meta or is_icici_header:
        return 'icici', 0.95, headers, samples

    # B. Axis Detection:
    is_axis_meta = 'axis bank' in top_metadata or ('axis' in top_metadata and 'account' in top_metadata)
    is_axis_header = ('tran date' in header_str and 'chqno' in header_str) or \
                     ('particulars' in header_str and 'dr' in header_str and 'cr' in header_str and 'bal' in header_str)
    if is_axis_meta or is_axis_header:
        return 'axis', 0.95, headers, samples

    # C. Kotak Mahindra Detection:
    is_kotak_meta = 'kotak mahindra' in top_metadata or 'kotak bank' in top_metadata or 'kotak' in top_metadata
    is_kotak_header = ('dr / cr' in header_str or 'dr/cr' in header_str) and ('amount' in header_str or 'balance' in header_str)
    if is_kotak_meta or is_kotak_header:
        return 'kotak', 0.95, headers, samples

    # D. HDFC Detection:
    is_hdfc_header = any('withdrawal amt' in h for h in header_lower) and \
                     any('closing balance' in h or 'deposit amt' in h for h in header_lower)
    is_hdfc_meta = 'hdfc bank' in top_metadata or ('hdfc' in top_metadata and 'account' in top_metadata)
    if is_hdfc_meta or is_hdfc_header:
        return 'hdfc', 0.95, headers, samples

    # E. SBI Detection:
    is_sbi_header = any('txn date' in h for h in header_lower) and \
                    any('ref no' in h or 'cheque no' in h for h in header_lower)
    is_sbi_meta = 'state bank of india' in top_metadata or 'sbi' in top_metadata
    if is_sbi_meta or is_sbi_header:
        return 'sbi', 0.95, headers, samples

    # F. Generic CSV Detection
    date_keywords = ['date', 'dt', 'time', 'timestamp', 'day', 'period', 'posting', 'value']
    amount_keywords = ['amount', 'amt', 'debit', 'credit', 'withdrawal', 'deposit', 'spent', 'received', 'dr', 'cr', 'paid', 'payment', 'inflow', 'outflow']
    balance_keywords = ['balance', 'bal', 'closing']

    has_date = any(any(k in h for k in date_keywords) for h in header_lower)
    has_amount = any(any(k in h for k in amount_keywords) for h in header_lower)
    has_balance = any(any(k in h for k in balance_keywords) for h in header_lower)

    if (has_date and (has_amount or has_balance)) or (has_amount and has_balance):
        return 'generic', 0.90, headers, samples

    if headers and len(headers) >= 3:
        # If there are 3+ columns and any amount or date keyword, treat as generic statement
        if has_date or has_amount:
            return 'generic', 0.80, headers, samples
        return 'unknown', 0.4, headers, samples

    return 'unknown', 0.0, [], []

def _extract_headers_and_samples(lines: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Locates CSV header and extracts sample rows with multi-delimiter resilience."""
    best_cols = []
    best_samples = []
    best_score = -1

    delims = [',', ';', '\t', '|']
    for idx, line in enumerate(lines[:60]):
        delim_counts = {d: line.count(d) for d in delims}
        max_delim = max(delim_counts, key=delim_counts.get)
        if delim_counts[max_delim] >= 1:
            try:
                csv_block = "\n".join(lines[idx:idx + 8])
                df = pd.read_csv(io.StringIO(csv_block), sep=max_delim, dtype=str, on_bad_lines='skip')
                if len(df.columns) >= 2:
                    col_names = [str(c).strip() for c in df.columns]
                    low_cols = [c.lower() for c in col_names]
                    col_str = ' '.join(low_cols)
                    keywords = [
                        'date', 'dt', 'time', 'day', 'narration', 'particular', 'desc', 'detail',
                        'remark', 'debit', 'credit', 'amount', 'amt', 'balance', 'bal', 'dr', 'cr',
                        'withdrawal', 'deposit', 'chq', 'ref', 'chqno', 'tran'
                    ]
                    score = sum(1 for kw in keywords if kw in col_str)
                    if score > best_score and score >= 2:
                        best_score = score
                        best_cols = col_names
                        best_samples = df.head(5).fillna('').to_dict(orient='records')
                        if score >= 4:
                            return best_cols, best_samples
            except Exception:
                continue

    if best_cols:
        return best_cols, best_samples
    return [], []
