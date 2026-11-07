import io
import re
import pandas as pd
from typing import List, Optional
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction, ColumnMapping

class GenericCSVParser(BaseParser):
    """
    Parser for generic bank statement CSVs.
    Can operate in:
      1. Auto-detection mode (matches synonymous column headers & multi-delimiter resilience).
      2. Explicit user column mapping mode.
    """

    def __init__(self, mapping: Optional[ColumnMapping] = None):
        self.mapping = mapping

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        text = content.decode('utf-8', errors='ignore')
        lines = [line for line in text.splitlines() if line.strip()]

        if not lines:
            return []

        # Find header index: the row with the most column-like delimiters
        header_idx = 0
        detected_sep = ','
        delims = [',', ';', '\t', '|']

        if not self.mapping:
            best_score = -1
            for idx, line in enumerate(lines[:60]):
                low = line.lower()
                delim_counts = {d: line.count(d) for d in delims}
                max_d = max(delim_counts, key=delim_counts.get)
                if delim_counts[max_d] >= 1:
                    keywords = [
                        'date', 'dt', 'time', 'day', 'narration', 'particular', 'desc', 'detail',
                        'remark', 'debit', 'credit', 'amount', 'amt', 'balance', 'bal', 'dr', 'cr',
                        'withdrawal', 'deposit', 'chq', 'ref', 'chqno', 'tran'
                    ]
                    score = sum(1 for kw in keywords if kw in low)
                    if score > best_score and score >= 2:
                        best_score = score
                        header_idx = idx
                        detected_sep = max_d
                        if score >= 4:
                            break
        else:
            delim_counts = {d: lines[0].count(d) for d in delims}
            detected_sep = max(delim_counts, key=delim_counts.get)

        csv_data = "\n".join(lines[header_idx:])
        try:
            df = pd.read_csv(io.StringIO(csv_data), sep=detected_sep, dtype=str, on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(io.StringIO(csv_data), dtype=str, on_bad_lines='skip')
            except Exception:
                return []

        # Build column mapping
        date_col = None
        desc_col = None
        debit_col = None
        credit_col = None
        amount_col = None
        balance_col = None
        date_format = None

        if self.mapping:
            date_col = self.mapping.date_col
            desc_col = self.mapping.description_col
            debit_col = self.mapping.debit_col
            credit_col = self.mapping.credit_col
            amount_col = self.mapping.amount_col
            balance_col = self.mapping.balance_col
            date_format = self.mapping.date_format
        else:
            for col in df.columns:
                c = str(col).strip().lower()
                if not date_col and (re.search(r'\b(?:date|dt|time|day|period|posting|value|timestamp)\b', c) or 'date' in c):
                    date_col = col
                elif not desc_col and (re.search(r'\b(?:desc|narration|particular|memo|detail|remark|txn|trans|party|payee|reference)\b', c) or any(k in c for k in ['desc', 'narration', 'particular', 'memo', 'detail'])):
                    desc_col = col
                elif not debit_col and (re.search(r'\b(?:debit|withdrawal|spent|dr|outflow|payment)\b', c) or any(k in c for k in ['debit', 'withdrawal', 'dr', 'spent'])):
                    debit_col = col
                elif not credit_col and (re.search(r'\b(?:credit|deposit|received|cr|inflow|receipt)\b', c) or any(k in c for k in ['credit', 'deposit', 'cr', 'received'])):
                    credit_col = col
                elif not amount_col and (re.search(r'\b(?:amount|amt)\b', c) or 'amount' in c):
                    amount_col = col
                elif not balance_col and (re.search(r'\b(?:balance|bal|closing)\b', c) or any(k in c for k in ['balance', 'bal', 'closing'])):
                    balance_col = col

            # Fallbacks if columns weren't matched by keyword
            if not date_col and len(df.columns) > 0:
                date_col = df.columns[0]
            if not desc_col and len(df.columns) > 1:
                desc_col = df.columns[1]

        transactions: List[NormalizedTransaction] = []
        running_bal = 0.0
        has_explicit_balance = bool(balance_col and balance_col in df.columns and balance_col != '(AUTO_COMPUTE)')

        for idx, row in df.iterrows():
            raw_date = str(row.get(date_col, '')).strip() if date_col in df.columns else ""
            parsed_date = self.parse_date(raw_date, custom_format=date_format)

            if not parsed_date:
                if raw_date and raw_date.lower() not in ('nan', 'none', '-', '', 'null'):
                    parsed_date = raw_date
                else:
                    continue

            desc = str(row.get(desc_col, '')).strip() if desc_col in df.columns else "Transaction"
            if not desc or desc.lower() == 'nan':
                desc = "Generic Transaction"

            debit = 0.0
            credit = 0.0

            if debit_col and debit_col in df.columns:
                debit = self.clean_amount(row.get(debit_col))
            if credit_col and credit_col in df.columns:
                credit = self.clean_amount(row.get(credit_col))

            # Handle single signed amount column if separate debit/credit columns are missing
            if debit == 0.0 and credit == 0.0 and amount_col and amount_col in df.columns:
                raw_amt = str(row.get(amount_col, '')).strip()
                amt_val = self.clean_amount(raw_amt)
                if '-' in raw_amt or 'dr' in raw_amt.lower():
                    debit = amt_val
                else:
                    credit = amt_val

            balance = 0.0
            if has_explicit_balance:
                balance = self.clean_amount(row.get(balance_col))
                running_bal = balance
            else:
                running_bal += (credit - debit)
                balance = round(running_bal, 2)

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            csv_row_num = header_idx + 2 + int(idx)
            raw_line = lines[header_idx + 1 + int(idx)] if (header_idx + 1 + int(idx)) < len(lines) else ", ".join(f"{k}:{v}" for k, v in row.items())

            tx = NormalizedTransaction(
                id=f"gen-{idx+1}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                source_page=1,
                source_row=csv_row_num,
                raw_text=raw_line,
                extraction_confidence=1.0
            )
            transactions.append(tx)

        return transactions

