import re
from typing import Optional

class DataSanitizer:
    """
    Sanitizes personally identifiable information (PII) from banking statements.
    Masks bank account numbers, debit/credit cards, PAN numbers, and phone numbers.
    """

    @classmethod
    def mask_sensitive_data(cls, text: Optional[str]) -> str:
        if not text:
            return ""

        clean = str(text)

        # 1. Mask 10 to 18 digit bank account numbers (keep last 4 digits)
        clean = re.sub(
            r'\b(\d{6,14})(\d{4})\b',
            r'••••\2',
            clean
        )

        # 2. Mask 16-digit credit card patterns (XXXX-XXXX-XXXX-1234 or spaced)
        clean = re.sub(
            r'\b(?:\d{4}[-\s]?){3}(\d{4})\b',
            r'••••••••••••\1',
            clean
        )

        # 3. Mask Indian PAN Cards: 5 uppercase letters, 4 digits, 1 letter (e.g. ABCDE1234F -> AB••••34F)
        clean = re.sub(
            r'\b([A-Z]{2})[A-Z]{3}\d{2}(\d{2}[A-Z])\b',
            r'\1••••\2',
            clean
        )

        # 4. Mask 10-digit Indian mobile numbers (+91-9876543210 or 9876543210 -> ••••3210)
        clean = re.sub(
            r'(?:\+91[-.\s]?)?[6-9]\d{5}(\d{4})\b',
            r'••••\1',
            clean
        )

        return clean

