import re
from typing import Optional, Dict

class DataSanitizer:
    """
    Sanitizes personally identifiable information (PII) from banking statements.
    Masks bank account numbers, debit/credit cards, PAN numbers, and phone numbers.
    Maintains deterministic audit counters of masked tokens.
    """
    _masked_count: int = 0
    _patterns_breakdown: Dict[str, int] = {
        "bank_accounts": 0,
        "credit_cards": 0,
        "pan_cards": 0,
        "phone_numbers": 0
    }

    @classmethod
    def get_masked_count(cls) -> int:
        return cls._masked_count

    @classmethod
    def get_breakdown(cls) -> Dict[str, int]:
        return dict(cls._patterns_breakdown)

    @classmethod
    def reset_counter(cls) -> None:
        cls._masked_count = 0
        cls._patterns_breakdown = {
            "bank_accounts": 0,
            "credit_cards": 0,
            "pan_cards": 0,
            "phone_numbers": 0
        }

    @classmethod
    def compute_effective_masked_count(cls, db_session=None) -> int:
        """
        Returns the runtime counter if > 0; if 0 and db_session is provided,
        computes actual masked token patterns stored in SQLite records.
        """
        if cls._masked_count > 0:
            return cls._masked_count

        if db_session:
            try:
                from app.models.transaction import TransactionModel
                txs = db_session.query(TransactionModel.description, TransactionModel.raw_text).all()
                count = 0
                for desc, raw in txs:
                    if desc:
                        count += desc.count("••••")
                    if raw:
                        count += raw.count("••••")
                return count
            except Exception:
                pass
        return 0

    @classmethod
    def mask_sensitive_data(cls, text: Optional[str]) -> str:
        if not text:
            return ""

        clean = str(text)

        # 1. Mask 16-digit credit card patterns (XXXX-XXXX-XXXX-1234 or spaced)
        clean, n2 = re.subn(
            r'\b(?:\d{4}[-\s]?){3}(\d{4})\b',
            r'••••••••••••\1',
            clean
        )

        # 2. Mask Indian PAN Cards: 5 uppercase letters, 4 digits, 1 letter (e.g. ABCDE1234F -> AB••••34F)
        clean, n3 = re.subn(
            r'\b([A-Z]{2})[A-Z]{3}\d{2}(\d{2}[A-Z])\b',
            r'\1••••\2',
            clean
        )

        # 3. Mask 10-digit Indian mobile numbers (+91-9876543210 or 9876543210 -> ••••3210)
        clean, n4 = re.subn(
            r'(?:\+91[-.\s]?)?[6-9]\d{5}(\d{4})\b',
            r'••••\1',
            clean
        )

        # 4. Mask 10 to 18 digit bank account numbers (keep last 4 digits)
        clean, n1 = re.subn(
            r'\b(\d{6,14})(\d{4})\b',
            r'••••\2',
            clean
        )

        cls._patterns_breakdown["credit_cards"] += n2
        cls._patterns_breakdown["pan_cards"] += n3
        cls._patterns_breakdown["phone_numbers"] += n4
        cls._patterns_breakdown["bank_accounts"] += n1
        cls._masked_count += (n1 + n2 + n3 + n4)

        return clean
