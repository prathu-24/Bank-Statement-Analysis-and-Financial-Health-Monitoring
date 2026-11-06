import io
import re
from typing import List, Optional, Dict
import pdfplumber
from app.parsers.base import BaseParser
from app.schemas.transaction import NormalizedTransaction

class PDFParser(BaseParser):
    """
    Parser for Bank Statement PDF documents.
    Features:
      1. Robust multi-page statement extraction.
      2. Wrapped multi-line description stitching across table row fragments.
      3. Friendly actionable response for password-protected / encrypted PDFs.
      4. Clear guidance for scanned or image-only PDFs.
    """

    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        if not content or len(content) < 10:
            return []

        transactions: List[NormalizedTransaction] = []
        is_password_protected = False

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                total_pages = len(pdf.pages)
                all_extracted_text = []

                for page_idx, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    all_extracted_text.append(page_text)

                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        txs = self._parse_table(table, page_idx, transactions)
                        transactions.extend(txs)

                # Check if document was scanned/image-only
                full_text_combined = " ".join(all_extracted_text).strip()
                if not transactions and len(full_text_combined) < 25 and total_pages > 0:
                    raise ValueError(
                        "Scanned or image-only PDF detected: FinSight requires digital text-based or tabular PDF statements. "
                        "Please upload the official digital e-statement generated directly by your banking portal."
                    )

                # Fallback to regex line-by-line if tables could not be parsed
                if not transactions and len(full_text_combined) >= 25:
                    transactions = self._parse_raw_text(full_text_combined)

        except Exception as e:
            err_msg = str(e).lower()
            if "password" in err_msg or "encrypt" in err_msg or "auth" in err_msg:
                raise ValueError("Password required: This PDF statement is password-protected. Please provide an unlocked document.")
            if "scanned or image-only" in err_msg:
                raise
            if not transactions:
                raise ValueError(f"Failed to parse PDF bank statement: {str(e)}")

        return transactions

    def _parse_table(
        self,
        table: List[List[Optional[str]]],
        page_idx: int,
        existing_txs: List[NormalizedTransaction]
    ) -> List[NormalizedTransaction]:
        txs: List[NormalizedTransaction] = []

        # Find header row
        header_idx = -1
        col_indices: Dict[str, int] = {}

        for row_idx, row in enumerate(table[:6]):
            row_str = " ".join([str(c or '').lower() for c in row])
            if any(w in row_str for w in ['date', 'txn', 'transaction']) and \
               any(w in row_str for w in ['balance', 'debit', 'credit', 'amount', 'narration', 'particulars']):
                header_idx = row_idx
                for c_idx, cell in enumerate(row):
                    val = str(cell or '').strip().lower()
                    if 'date' in val and 'value' not in val:
                        col_indices['date'] = c_idx
                    elif any(w in val for w in ['narration', 'description', 'particulars', 'details', 'remarks']):
                        col_indices['desc'] = c_idx
                    elif any(w in val for w in ['debit', 'withdrawal', 'dr']):
                        col_indices['debit'] = c_idx
                    elif any(w in val for w in ['credit', 'deposit', 'cr']):
                        col_indices['credit'] = c_idx
                    elif any(w in val for w in ['balance', 'closing', 'bal']):
                        col_indices['balance'] = c_idx
                break

        if header_idx == -1 or 'date' not in col_indices:
            return []

        for row_idx, row in enumerate(table[header_idx + 1:], start=header_idx + 1):
            if not row or len(row) <= max(col_indices.values()):
                continue

            raw_date = row[col_indices['date']]
            parsed_date = self.parse_date(raw_date)

            desc = ""
            if 'desc' in col_indices and col_indices['desc'] < len(row):
                desc = str(row[col_indices['desc']] or '').strip().replace('\n', ' ')

            debit = 0.0
            if 'debit' in col_indices and col_indices['debit'] < len(row):
                debit = self.clean_amount(row[col_indices['debit']])

            credit = 0.0
            if 'credit' in col_indices and col_indices['credit'] < len(row):
                credit = self.clean_amount(row[col_indices['credit']])

            balance = 0.0
            if 'balance' in col_indices and col_indices['balance'] < len(row):
                balance = self.clean_amount(row[col_indices['balance']])

            # Wrapped description continuation handling:
            # If date is absent, but there is text and debit/credit/balance are 0,
            # this row is a wrapped narration fragment of the immediately preceding transaction!
            if not parsed_date and desc and debit == 0.0 and credit == 0.0 and balance == 0.0:
                last_tx = txs[-1] if txs else (existing_txs[-1] if existing_txs else None)
                if last_tx:
                    last_tx.description = (last_tx.description + " " + desc).strip()
                continue

            if not parsed_date:
                continue

            if debit == 0.0 and credit == 0.0 and balance == 0.0:
                continue

            if not desc:
                desc = "PDF Statement Transaction"

            raw_row_line = " | ".join([str(c or '').strip() for c in row])

            tx = NormalizedTransaction(
                id=f"pdf-p{page_idx+1}-r{row_idx}",
                date=parsed_date,
                description=desc,
                debit=debit,
                credit=credit,
                balance=balance,
                category="Uncategorized",
                source_page=page_idx + 1,
                source_row=row_idx + 1,
                raw_text=raw_row_line,
                extraction_confidence=1.0
            )
            txs.append(tx)

        return txs

    def _parse_raw_text(self, text: str) -> List[NormalizedTransaction]:
        """Line-by-line fallback using common Indian bank statement text patterns."""
        txs: List[NormalizedTransaction] = []
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

                debit = amt1 if 'dr' in line.lower() or amt2 == 0.0 else 0.0
                credit = amt2 if debit == 0.0 else 0.0

                txs.append(NormalizedTransaction(
                    id=f"pdf-line-{idx+1}",
                    date=parsed_date,
                    description=raw_desc.strip(),
                    debit=debit,
                    credit=credit,
                    balance=balance,
                    category="Uncategorized",
                    source_page=1,
                    source_row=idx + 1,
                    raw_text=line,
                    extraction_confidence=0.85
                ))

        return txs
