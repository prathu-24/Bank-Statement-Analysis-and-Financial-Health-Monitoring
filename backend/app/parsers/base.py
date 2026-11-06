from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
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
        If allow_negative is True, preserves negative sign if present so validator can catch malformed data.
        """
        if value is None:
            return 0.0
        
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('nan', 'none', '-', '', 'null'):
            return 0.0

        is_negative = '-' in val_str

        # Remove currency symbols (₹, $, Rs., etc.) and commas
        cleaned = re.sub(r'[₹$€£\s,]|(?:rs\.?)|(?:inr)', '', val_str, flags=re.IGNORECASE)
        # Handle Cr / Dr suffix if present
        cleaned = re.sub(r'(?:cr|dr)\.?$', '', cleaned, flags=re.IGNORECASE).strip()
        # Remove any stray dashes except leading minus
        cleaned = re.sub(r'[^\d.-]', '', cleaned)

        try:
            val = float(cleaned)
            if is_negative and allow_negative:
                return -abs(val)
            return abs(val)
        except ValueError:
            return 0.0

    @classmethod
    def parse_date(cls, value: Any, custom_format: Optional[str] = None) -> Optional[str]:
        """
        Parses multiple standard banking date formats into ISO format YYYY-MM-DD.
        """
        if not value:
            return None
        
        val_str = str(value).strip()
        if not val_str or val_str.lower() in ('nan', 'none', '-', 'null'):
            return None

        # Clean extraneous spaces or time components if present
        date_part = re.split(r'[\sT]', val_str)[0].strip()

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
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d %b %Y',
            '%d-%b-%Y',
            '%d %B %Y',
            '%d-%B-%Y',
            '%d-%b-%y',
            '%d %b %y',
            '%b %d, %Y',
            '%m/%d/%Y',
        ]

        for fmt in known_formats:
            try:
                dt = datetime.strptime(date_part, fmt)
                # Sanity check year: banking statements generally fall between 1990 and 2099
                if 1990 <= dt.year <= 2099:
                    return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

