import io
import re
import pandas as pd
from typing import List
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class AxisParser(BaseParser):
    """
    Parser for Axis Bank Statement CSV exports.
    Handles Axis metadata headers and standard abbreviations:
      Tran Date -> Date
      CHQNO -> Reference ID
      PARTICULARS -> Description
      DR -> Debit
      CR -> Credit
      BAL -> Balance
    """

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        if not content or not content.strip():
            return []

        try:
            text = content.decode('utf-8', errors='ignore')
        except Exception:
            return []

        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            return []

        # Find header row
        header_idx = -1
        for idx, line in enumerate(lines[:35]):
            lower = line.lower()
            if ('tran date' in lower or 'date' in lower) and \
               ('particular' in lower or 'desc' in lower or 'dr' in lower or 'cr' in lower or 'bal' in lower):
                header_idx = idx
                break

        if header_idx == -1:
            header_idx = 0

        csv_data = "\n".join(lines[header_idx:])
        try:
            df = pd.read_csv(io.StringIO(csv_data), dtype=str)
        except Exception:
            return []

        col_map = {}
        for col in df.columns:
            c_clean = str(col).strip().lower()
            if c_clean in ('particulars', 'particular', 'description', 'narration'):
                col_map['description'] = col
            elif 'date' in c_clean and 'value' not in c_clean:
                col_map['date'] = col
            elif c_clean in ('dr', 'debit', 'withdrawal'):
                col_map['debit'] = col
            elif c_clean in ('cr', 'credit', 'deposit'):
                col_map['credit'] = col
            elif c_clean in ('bal', 'balance', 'closing balance'):
                col_map['balance'] = col
            elif c_clean in ('chqno', 'chq no', 'ref no', 'reference'):
                col_map['ref'] = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get('date', ''))
            parsed_date = self.parse_date(raw_date)
            if not parsed_date:
                continue

            desc = str(row.get(col_map.get('description', ''), '')).strip()
            if not desc or desc.lower() == 'nan':
                desc = "Axis Bank Transaction"

            debit = self.clean_amount(row.get(col_map.get('debit', '')))
            credit = self.clean_amount(row.get(col_map.get('credit', '')))
            balance = self.clean_amount(row.get(col_map.get('balance', '')))
            ref_id = str(row.get(col_map.get('ref', ''), '')).strip()
            if ref_id.lower() in ('nan', 'none', '-'):
                ref_id = None

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            csv_row_num = header_idx + 2 + int(idx)
            raw_line = lines[header_idx + 1 + int(idx)] if (header_idx + 1 + int(idx)) < len(lines) else ", ".join(f"{k}:{v}" for k, v in row.items())

            tx = NormalizedTransaction(
                id=f"axis-{idx+1}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                reference_id=ref_id,
                source_page=1,
                source_row=csv_row_num,
                raw_text=raw_line,
                extraction_confidence=1.0,
                raw_row={k: str(v) for k, v in row.to_dict().items() if pd.notna(v)}
            )
            transactions.append(tx)

        return transactions
