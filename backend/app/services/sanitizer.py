import re
from typing import Optional, Dict

class DataSanitizer:
    """
    Sanitizes personally identifiable information (PII) from banking statements.
    Masks bank account numbers, credit/debit cards, PAN numbers, Aadhaar numbers,
    phone numbers, email addresses, and UPI IDs (VPAs).
    Explicitly guards financial amounts and calendar dates against false-positive masking.
    Maintains deterministic audit counters of masked tokens.
    """
    _masked_count: int = 0
    _patterns_breakdown: Dict[str, int] = {
        "bank_accounts": 0,
        "credit_cards": 0,
        "pan_cards": 0,
        "aadhaar_numbers": 0,
        "phone_numbers": 0,
        "emails": 0,
        "upi_ids": 0
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
            "aadhaar_numbers": 0,
            "phone_numbers": 0,
            "emails": 0,
            "upi_ids": 0
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

        # 1. Mask 16-digit credit/debit cards (XXXX-XXXX-XXXX-1234 or spaced or continuous)
        clean, n_card = re.subn(
            r'\b(?:\d{4}[-\s]?){3}(\d{4})\b',
            r'••••••••••••\1',
            clean
        )

        # 2. Mask 12-digit Indian Aadhaar numbers (XXXX XXXX 1234 or XXXX-XXXX-1234)
        clean, n_aadhaar = re.subn(
            r'\b\d{4}[-\s]\d{4}[-\s](\d{4})\b',
            r'••••••••\1',
            clean
        )

        # 3. Mask Indian PAN Cards: 5 uppercase letters, 4 digits, 1 letter (e.g. ABCDE1234F -> AB••••34F)
        clean, n_pan = re.subn(
            r'\b([A-Z]{2})[A-Z]{3}\d{2}(\d{2}[A-Z])\b',
            r'\1••••\2',
            clean
        )

        # 4. Mask UPI IDs / VPAs with bank/PSP handles (e.g. user@okhdfcbank -> us••••@okhdfcbank)
        clean, n_upi = re.subn(
            r'\b([a-zA-Z0-9.\-_]{2})[a-zA-Z0-9.\-_]*@(okhdfcbank|okaxis|oksbi|okicici|paytm|ybl|axl|ibl|apl|upi|barodampay|fbl|icici|hdfcbank|sbi|axisbank)\b',
            r'\1••••@\2',
            clean
        )

        # 5. Mask Email Addresses (e.g. user.name@domain.com -> us••••@domain.com)
        clean, n_email = re.subn(
            r'\b([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b',
            r'\1••••@\2',
            clean
        )

        # 6. Mask 10-digit Indian mobile numbers (+91-9876543210 or 9876543210 -> ••••3210)
        # Uses negative lookahead (?!\.\d) to prevent matching decimal amounts as phone numbers
        clean, n_phone = re.subn(
            r'(?<![\d\w])(?:\+91[-.\s]?)?[6-9]\d{5}(\d{4})\b(?!\.\d)',
            r'••••\1',
            clean
        )

        # 7. Mask 10 to 18 digit bank account numbers (keep last 4 digits)
        # Uses negative lookbehind (?<![₹$€£\d\w]) and lookahead (?!\.\d) to preserve monetary amounts
        clean, n_acct = re.subn(
            r'(?<![₹$€£\d\w])\b(\d{6,14})(\d{4})\b(?!\.\d)',
            r'••••\2',
            clean
        )

        cls._patterns_breakdown["credit_cards"] += n_card
        cls._patterns_breakdown["aadhaar_numbers"] += n_aadhaar
        cls._patterns_breakdown["pan_cards"] += n_pan
        cls._patterns_breakdown["upi_ids"] += n_upi
        cls._patterns_breakdown["emails"] += n_email
        cls._patterns_breakdown["phone_numbers"] += n_phone
        cls._patterns_breakdown["bank_accounts"] += n_acct

        total_new = n_card + n_aadhaar + n_pan + n_upi + n_email + n_phone + n_acct
        cls._masked_count += total_new

        return clean
