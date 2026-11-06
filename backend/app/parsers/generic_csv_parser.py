import io
import pandas as pd
from typing import List, Optional
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction, ColumnMapping

class GenericCSVParser(BaseParser):
    """
    Parser for generic bank statement CSVs.
    Can operate in:
      1. Auto-detection mode (matches synonymous column headers).
      2. Explicit user column mapping mode.
    """

    def __init__(self, mapping: Optional[ColumnMapping] = None):
        self.mapping = mapping

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        text = content.decode('utf-8', errors='ignore')
        lines = [line for line in text.splitlines() if line.strip()]

        if not lines:
            return []

        # Find header index: the row with the most column-like commas/delimiters
        header_idx = 0
        if not self.mapping:
            for idx, line in enumerate(lines[:15]):
                low = line.lower()
                if any(w in low for w in ['date', 'amount', 'balance', 'description', 'debit', 'credit']):
                    header_idx = idx
                    break

        csv_data = "\n".join(lines[header_idx:])
        df = pd.read_csv(io.StringIO(csv_data), dtype=str)

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
                if not date_col and ('date' in c or 'txn_date' in c):
                    date_col = col
                elif not desc_col and any(k in c for k in ['desc', 'narration', 'particular', 'memo', 'details', 'name']):
                    desc_col = col
                elif not debit_col and any(k in c for k in ['debit', 'withdrawal', 'dr', 'spent']):
                    debit_col = col
                elif not credit_col and any(k in c for k in ['credit', 'deposit', 'cr', 'received']):
                    credit_col = col
                elif not amount_col and 'amount' in c:
                    amount_col = col
                elif not balance_col and any(k in c for k in ['balance', 'bal', 'closing']):
                    balance_col = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(date_col) if date_col in df.columns else None
            parsed_date = self.parse_date(raw_date, custom_format=date_format)

            if not parsed_date:
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
            if balance_col and balance_col in df.columns:
                balance = self.clean_amount(row.get(balance_col))

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            tx = NormalizedTransaction(
                id=f"gen-{idx+1}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                raw_row={k: str(v) for k, v in row.to_dict().items() if pd.notna(v)}
            )
            transactions.append(tx)

        return transactions

