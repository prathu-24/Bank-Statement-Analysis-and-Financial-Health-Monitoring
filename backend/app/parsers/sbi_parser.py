import io
import pandas as pd
from typing import List
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class SBIParser(BaseParser):
    """
    Parser for State Bank of India (SBI) Statement CSV exports.
    Handles SBI's header blocks and standard column mapping:
      Txn Date -> Date
      Description -> Description
      Ref No./Cheque No. -> Reference ID
      Debit -> Debit
      Credit -> Credit
      Balance -> Balance
    """

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        text = content.decode('utf-8', errors='ignore')
        lines = text.splitlines()

        # Locate table header
        header_idx = -1
        for idx, line in enumerate(lines[:35]):
            lower = line.lower()
            if ('txn date' in lower or 'txndate' in lower) and \
               ('description' in lower or 'debit' in lower or 'balance' in lower):
                header_idx = idx
                break

        if header_idx == -1:
            # Fallback to checking line with debit, credit, balance
            for idx, line in enumerate(lines[:30]):
                lower = line.lower()
                if 'debit' in lower and 'credit' in lower and 'balance' in lower:
                    header_idx = idx
                    break

        if header_idx == -1:
            header_idx = 0

        csv_data = "\n".join(lines[header_idx:])
        df = pd.read_csv(io.StringIO(csv_data), dtype=str)

        col_map = {}
        for col in df.columns:
            c_clean = str(col).strip().lower()
            if 'txn date' in c_clean or (c_clean.startswith('date') and 'value' not in c_clean):
                col_map['date'] = col
            elif 'description' in c_clean or 'particulars' in c_clean or 'remarks' in c_clean:
                col_map['description'] = col
            elif 'debit' in c_clean:
                col_map['debit'] = col
            elif 'credit' in c_clean:
                col_map['credit'] = col
            elif 'balance' in c_clean:
                col_map['balance'] = col
            elif 'ref' in c_clean or 'cheque' in c_clean or 'chq' in c_clean:
                col_map['ref'] = col

        transactions: List[NormalizedTransaction] = []

        for idx, row in df.iterrows():
            raw_date = row.get(col_map.get('date', ''))
            parsed_date = self.parse_date(raw_date)
            
            # Skip non-transactional footer rows
            if not parsed_date:
                continue

            desc = str(row.get(col_map.get('description', ''), '')).strip()
            if not desc or desc.lower() == 'nan':
                desc = "Unknown SBI Transaction"

            debit = self.clean_amount(row.get(col_map.get('debit', '')))
            credit = self.clean_amount(row.get(col_map.get('credit', '')))
            balance = self.clean_amount(row.get(col_map.get('balance', '')))
            ref_id = str(row.get(col_map.get('ref', ''), '')).strip()
            if ref_id.lower() == 'nan':
                ref_id = None

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            tx = NormalizedTransaction(
                id=f"sbi-{idx+1}",
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

