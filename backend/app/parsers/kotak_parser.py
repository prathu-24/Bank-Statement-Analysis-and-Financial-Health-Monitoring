import io
import re
import pandas as pd
from typing import List
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class KotakParser(BaseParser):
    """
    Parser for Kotak Mahindra Bank Statement CSV exports.
    Handles Kotak format with either separate Debit/Credit columns
    or Kotak's standard single Amount with Dr / Cr indicator column:
      Transaction Date -> Date
      Narration / Description -> Description
      Chq / Ref No. -> Reference ID
      Amount + Dr / Cr -> Debit & Credit
      Balance -> Balance
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
            if ('date' in lower and ('narration' in lower or 'desc' in lower or 'particular' in lower)) or \
               ('amount' in lower and 'balance' in lower) or \
               ('dr / cr' in lower or 'dr/cr' in lower):
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
            if 'narration' in c_clean or 'description' in c_clean or 'particular' in c_clean:
                col_map['description'] = col
            elif 'date' in c_clean and 'value' not in c_clean:
                col_map['date'] = col
            elif 'debit' in c_clean or c_clean == 'dr':
                col_map['debit'] = col
            elif 'credit' in c_clean or c_clean == 'cr':
                col_map['credit'] = col
            elif 'dr / cr' in c_clean or 'dr/cr' in c_clean or c_clean == 'type':
                col_map['dr_cr'] = col
            elif 'amount' in c_clean:
                col_map['amount'] = col
            elif 'balance' in c_clean or 'bal' in c_clean:
                col_map['balance'] = col
            elif 'ref' in c_clean or 'chq' in c_clean:
                col_map['ref'] = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get('date', ''))
            parsed_date = self.parse_date(raw_date)
            if not parsed_date:
                continue

            desc = str(row.get(col_map.get('description', ''), '')).strip()
            if not desc or desc.lower() == 'nan':
                desc = "Kotak Mahindra Transaction"

            # Check if separate debit/credit or single signed amount with Dr/Cr column
            debit = 0.0
            credit = 0.0
            if 'debit' in col_map and 'credit' in col_map:
                debit = self.clean_amount(row.get(col_map['debit']))
                credit = self.clean_amount(row.get(col_map['credit']))
            elif 'amount' in col_map:
                raw_amt = row.get(col_map['amount'])
                dr_cr = row.get(col_map.get('dr_cr', ''))
                debit, credit = self.parse_signed_amount(raw_amt, dr_cr)

            balance = self.clean_amount(row.get(col_map.get('balance', '')))
            ref_id = str(row.get(col_map.get('ref', ''), '')).strip()
            if ref_id.lower() in ('nan', 'none', '-'):
                ref_id = None

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            csv_row_num = header_idx + 2 + int(idx)
            raw_line = lines[header_idx + 1 + int(idx)] if (header_idx + 1 + int(idx)) < len(lines) else ", ".join(f"{k}:{v}" for k, v in row.items())

            tx = NormalizedTransaction(
                id=f"kotak-{idx+1}",
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
