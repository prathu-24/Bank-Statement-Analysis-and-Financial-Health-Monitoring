import io
import re
import pandas as pd
from typing import List, Optional
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction, ColumnMapping

class ExcelParser(BaseParser):
    """
    Parser for Microsoft Excel (.xlsx and .xls) Bank Statement workbooks.
    Auto-detects statement headers across sheets, supports column mappings,
    handles Dr/Cr indicators and signed amounts.
    """

    def __init__(self, mapping: Optional[ColumnMapping] = None):
        self.mapping = mapping

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        if not content or len(content) < 10:
            return []

        try:
            excel_file = io.BytesIO(content)
            # Read first sheet
            df = pd.read_excel(excel_file, sheet_name=0, dtype=str)
        except Exception as e:
            raise ValueError(f"Failed to read Excel workbook: {str(e)}")

        if df.empty:
            return []

        # If top rows are metadata, locate the row with header names
        header_idx = -1
        for idx in range(min(25, len(df))):
            row_vals = [str(v).strip().lower() for v in df.iloc[idx].values if pd.notna(v)]
            row_str = " ".join(row_vals)
            if any(w in row_str for w in ['date', 'txn date']) and \
               any(w in row_str for w in ['balance', 'debit', 'credit', 'amount', 'narration', 'particular']):
                header_idx = idx
                break

        if header_idx != -1:
            # Re-read with detected header row
            excel_file.seek(0)
            try:
                df = pd.read_excel(excel_file, sheet_name=0, skiprows=header_idx + 1, dtype=str)
            except Exception:
                pass

        col_map = {}
        if self.mapping:
            col_map['date'] = self.mapping.date_col
            col_map['description'] = self.mapping.description_col
            col_map['debit'] = self.mapping.debit_col
            col_map['credit'] = self.mapping.credit_col
            col_map['amount'] = self.mapping.amount_col
            col_map['balance'] = self.mapping.balance_col
        else:
            for col in df.columns:
                c_clean = str(col).strip().lower()
                if not col_map.get('description') and any(k in c_clean for k in ['desc', 'narration', 'particular', 'remark', 'details']):
                    col_map['description'] = col
                elif not col_map.get('date') and ('date' in c_clean and 'value' not in c_clean):
                    col_map['date'] = col
                elif not col_map.get('debit') and any(k in c_clean for k in ['debit', 'withdrawal', 'dr', 'spent']):
                    col_map['debit'] = col
                elif not col_map.get('credit') and any(k in c_clean for k in ['credit', 'deposit', 'cr', 'received']):
                    col_map['credit'] = col
                elif not col_map.get('dr_cr') and any(k in c_clean for k in ['dr / cr', 'dr/cr', 'type']):
                    col_map['dr_cr'] = col
                elif not col_map.get('amount') and 'amount' in c_clean:
                    col_map['amount'] = col
                elif not col_map.get('balance') and any(k in c_clean for k in ['balance', 'bal', 'closing']):
                    col_map['balance'] = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get('date', ''))
            parsed_date = self.parse_date(raw_date)
            if not parsed_date:
                continue

            desc = str(row.get(col_map.get('description', ''), '')).strip()
            if not desc or desc.lower() == 'nan':
                desc = "Excel Statement Transaction"

            debit = 0.0
            credit = 0.0
            if col_map.get('debit') and col_map.get('credit'):
                debit = self.clean_amount(row.get(col_map['debit']))
                credit = self.clean_amount(row.get(col_map['credit']))
            elif col_map.get('amount'):
                raw_amt = row.get(col_map['amount'])
                dr_cr = row.get(col_map.get('dr_cr', ''))
                debit, credit = self.parse_signed_amount(raw_amt, dr_cr)

            balance = self.clean_amount(row.get(col_map.get('balance', '')))

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            row_num = int(idx) + 2 + (header_idx if header_idx != -1 else 0)
            tx = NormalizedTransaction(
                id=f"xlsx-{idx+1}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                source_page=1,
                source_row=row_num,
                raw_text=", ".join(f"{k}:{v}" for k, v in row.items() if pd.notna(v)),
                extraction_confidence=1.0,
                raw_row={k: str(v) for k, v in row.to_dict().items() if pd.notna(v)}
            )
            transactions.append(tx)

        return transactions
