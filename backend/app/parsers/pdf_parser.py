import io
import re
from typing import List, Optional, Dict
import pdfplumber
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class PDFParser(BaseParser):
    """
    Parser for Bank Statement PDF documents.
    Extracts tabular data using pdfplumber and falls back to regex line analysis.
    """

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        transactions: List[NormalizedTransaction] = []

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        txs = self._parse_table(table, page_idx)
                        transactions.extend(txs)

            # If table extraction yielded no transactions, try text line regex
            if not transactions:
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                    transactions = self._parse_raw_text(full_text)

        except Exception as e:
            # Re-raise or return whatever was collected
            if not transactions:
                raise ValueError(f"Failed to parse PDF bank statement: {str(e)}")

        return transactions

    def _parse_table(self, table: List[List[Optional[str]]], page_idx: int) -> List[NormalizedTransaction]:
        txs: List[NormalizedTransaction] = []

        # Find header row
        header_idx = -1
        col_indices: Dict[str, int] = {}

        for row_idx, row in enumerate(table[:5]):
            row_str = " ".join([str(c or '').lower() for c in row])
            if any(w in row_str for w in ['date', 'txn', 'transaction']) and \
               any(w in row_str for w in ['balance', 'debit', 'credit', 'amount', 'narration', 'particulars']):
                header_idx = row_idx
                for c_idx, cell in enumerate(row):
                    val = str(cell or '').strip().lower()
                    if 'date' in val and 'value' not in val:
                        col_indices['date'] = c_idx
                    elif any(w in val for w in ['narration', 'description', 'particulars', 'details']):
                        col_indices['desc'] = c_idx
                    elif any(w in val for w in ['debit', 'withdrawal', 'dr']):
                        col_indices['debit'] = c_idx
                    elif any(w in val for w in ['credit', 'deposit', 'cr']):
                        col_indices['credit'] = c_idx
                    elif any(w in val for w in ['balance', 'closing']):
                        col_indices['balance'] = c_idx
                break

        if header_idx == -1 or 'date' not in col_indices:
            return []

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or len(row) <= max(col_indices.values()):
                continue

            raw_date = row[col_indices['date']]
            parsed_date = self.parse_date(raw_date)
            if not parsed_date:
                continue

            desc = ""
            if 'desc' in col_indices and col_indices['desc'] < len(row):
                desc = str(row[col_indices['desc']] or '').strip()
            if not desc:
                desc = "PDF Statement Transaction"

            debit = 0.0
            if 'debit' in col_indices and col_indices['debit'] < len(row):
                debit = self.clean_amount(row[col_indices['debit']])

            credit = 0.0
            if 'credit' in col_indices and col_indices['credit'] < len(row):
                credit = self.clean_amount(row[col_indices['credit']])

            balance = 0.0
            if 'balance' in col_indices and col_indices['balance'] < len(row):
                balance = self.clean_amount(row[col_indices['balance']])

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            tx = NormalizedTransaction(
                id=f"pdf-p{page_idx+1}-r{row_idx}",
                date=parsed_date,
                description=desc.replace('\n', ' '),
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized"
            )
            txs.append(tx)

        return txs

    def _parse_raw_text(self, text: str) -> List[NormalizedTransaction]:
        """Line-by-line fallback using common Indian bank statement text patterns."""
        txs: List[NormalizedTransaction] = []
        # Pattern: Date (DD/MM/YYYY or DD-MM-YYYY) + Narration + Debit/Credit + Balance
        line_pattern = re.compile(
            r'(\d{2}[/-]\d{2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+(?:\.\d{2})?)\s+([\d,]+(?:\.\d{2})?)\s+([\d,]+(?:\.\d{2})?)'
        )

        for idx, line in enumerate(text.splitlines()):
            line = line.strip()
            match = line_pattern.search(line)
            if match:
                raw_date, raw_desc, col1, col2, col3 = match.groups()
                parsed_date = self.parse_date(raw_date)
                if not parsed_date:
                    continue

                amt1 = self.clean_amount(col1)
                amt2 = self.clean_amount(col2)
                balance = self.clean_amount(col3)

                # Assume col1 = debit, col2 = credit if both present, or infer
                debit = amt1 if 'dr' in line.lower() or amt2 == 0.0 else 0.0
                credit = amt2 if debit == 0.0 else 0.0

                txs.append(NormalizedTransaction(
                    id=f"pdf-line-{idx+1}",
                    date=parsed_date,
                    description=raw_desc.strip(),
                    debit=debit,
                    credit=credit,
                    balance=balance,
                    category="Uncategorized"
                ))

        return txs

