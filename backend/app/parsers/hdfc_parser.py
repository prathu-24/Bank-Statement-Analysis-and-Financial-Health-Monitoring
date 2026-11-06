import io
import re
import pandas as pd
from typing import List
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class HDFCParser(BaseParser):
    """
    Parser for HDFC Bank Statement CSV exports.
    Handles metadata header rows, narration cleanup, and column mapping:
      Date -> Date
      Narration -> Description
      Chq./Ref.No. -> Reference ID
      Withdrawal Amt. -> Debit
      Deposit Amt. -> Credit
      Closing Balance -> Balance
    """

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        text = content.decode('utf-8', errors='ignore')
        lines = text.splitlines()

        # Find header row
        header_idx = -1
        for idx, line in enumerate(lines[:30]):
            lower = line.lower()
            if ('date' in lower and 'narration' in lower) or \
               ('withdrawal amt' in lower or 'deposit amt' in lower or 'closing balance' in lower):
                header_idx = idx
                break

        if header_idx == -1:
            header_idx = 0

        # Read CSV from detected header
        csv_data = "\n".join(lines[header_idx:])
        df = pd.read_csv(io.StringIO(csv_data), dtype=str)

        # Normalize column names
        col_map = {}
        for col in df.columns:
            c_clean = str(col).strip().lower()
            if 'narration' in c_clean or 'particulars' in c_clean:
                col_map['description'] = col
            elif 'date' in c_clean and 'value' not in c_clean:
                col_map['date'] = col
            elif 'withdrawal' in c_clean or 'debit' in c_clean:
                col_map['debit'] = col
            elif 'deposit' in c_clean or 'credit' in c_clean:
                col_map['credit'] = col
            elif 'balance' in c_clean:
                col_map['balance'] = col
            elif 'chq' in c_clean or 'ref' in c_clean:
                col_map['ref'] = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get('date', ''))
            parsed_date = self.parse_date(raw_date)
            
            # Skip rows where date is absent or malformed (likely footer/disclaimer rows)
            if not parsed_date:
                continue

            desc = str(row.get(col_map.get('description', ''), '')).strip()
            if not desc or desc.lower() == 'nan':
                desc = "Unknown HDFC Transaction"

            debit = self.clean_amount(row.get(col_map.get('debit', '')))
            credit = self.clean_amount(row.get(col_map.get('credit', '')))
            balance = self.clean_amount(row.get(col_map.get('balance', '')))
            ref_id = str(row.get(col_map.get('ref', ''), '')).strip()
            if ref_id.lower() == 'nan':
                ref_id = None

            # Skip empty transaction rows where both debit and credit are 0 and balance is 0
            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            tx = NormalizedTransaction(
                id=f"hdfc-{idx+1}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                reference_id=ref_id,
                raw_row={k: str(v) for k, v in row.to_dict().items() if pd.notna(v)}
            )
            transactions.append(tx)

        return transactions

