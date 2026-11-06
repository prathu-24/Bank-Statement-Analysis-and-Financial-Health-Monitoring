from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import re
from datetime import datetime
from app.schemas.transaction import NormalizedTransaction

class BaseParser(ABC):
    """
    Abstract Base Class for all bank statement parsers.
    Standardizes transaction normalization, date parsing, and currency parsing.
    """

    @abstractmethod
    def parse(self, content: bytes, filename: str = "") -> List[NormalizedTransaction]:
        """Parse raw file bytes into normalized transactions."""
        pass

    @classmethod
    def clean_amount(cls, value: Any, allow_negative: bool = True) -> float:
        """
        Cleans and normalizes monetary values.
        Handles currency symbols, thousands separators (commas), CR/DR tags, whitespace.
        If allow_negative is True, preserves negative sign if present.
        """
        if value is None:
            return 0.0
        
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('nan', 'none', '-', '', 'null'):
            return 0.0

        is_negative = '-' in val_str or '(' in val_str and ')' in val_str

        # Remove currency symbols (₹, $, Rs., etc.) and commas
        cleaned = re.sub(r'[₹$€£\s,]|(?:rs\.?)|(?:inr)', '', val_str, flags=re.IGNORECASE)
        # Handle Cr / Dr suffix if present
        cleaned = re.sub(r'(?:cr|dr)\.?$', '', cleaned, flags=re.IGNORECASE).strip()
        # Remove any stray dashes or parentheses except leading minus
        cleaned = re.sub(r'[^\d.-]', '', cleaned)

        try:
            val = float(cleaned)
            if is_negative and allow_negative:
                return -abs(val)
            return abs(val)
        except ValueError:
            return 0.0

    @classmethod
    def parse_signed_amount(cls, amount_val: Any, type_indicator: Optional[str] = None) -> Tuple[float, float]:
        """
        Parses an amount into a (debit, credit) tuple using an optional Dr/Cr indicator
        or embedded signed characters (- / +).
        """
        amt = cls.clean_amount(amount_val, allow_negative=True)
        raw_indicator = str(type_indicator or "").strip().lower()

        # 1. Indicator column has explicit 'dr' or 'cr'
        if 'dr' in raw_indicator:
            return (abs(amt), 0.0)
        if 'cr' in raw_indicator:
            return (0.0, abs(amt))

        # 2. Check embedded negative or sign in amount string
        raw_amt_str = str(amount_val or "").strip().lower()
        if '-' in raw_amt_str or amt < 0 or 'dr' in raw_amt_str:
            return (abs(amt), 0.0)
        if '+' in raw_amt_str or 'cr' in raw_amt_str:
            return (0.0, abs(amt))

        # Default: if positive and no indicator, default to credit if 0 debit
        return (abs(amt), 0.0) if amt > 0 else (0.0, 0.0)

    @classmethod
    def parse_date(cls, value: Any, custom_format: Optional[str] = None) -> Optional[str]:
        """
        Parses multiple standard banking date formats into ISO format YYYY-MM-DD.
        Supports DD/MM/YY, DD/MM/YYYY, DD-Mon-YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
        """
        if not value:
            return None
        
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('nan', 'none', '-', 'null'):
            return None

        # Clean extraneous spaces or time components if present
        date_part = re.split(r'[\sT]', val_str)[0].strip()
        # Remove trailing commas or periods
        date_part = date_part.rstrip(',. ')

        if custom_format:
            try:
                dt = datetime.strptime(date_part, custom_format)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

        known_formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%d-%m-%y',
            '%d.%m.%Y',
            '%d.%m.%y',
            '%d-%b-%Y',
            '%d-%b-%y',
            '%d %b %Y',
            '%d %b %y',
            '%d-%B-%Y',
            '%d-%B-%y',
            '%d %B %Y',
            '%d/%b/%Y',
            '%d/%b/%y',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%b %d, %Y',
            '%B %d, %Y',
            '%m/%d/%Y',
            '%m-%d-%Y',
        ]

        for fmt in known_formats:
            try:
                dt = datetime.strptime(date_part, fmt)
                if 1990 <= dt.year <= 2099:
                    return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None
