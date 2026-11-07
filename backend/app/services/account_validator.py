import re
from typing import Dict, Any, Optional, Tuple, List

class AccountValidator:
    """
    Forensic KYC and Account Authenticity Validation Engine.
    Detects and rejects fake, synthetic, or dummy bank accounts and account holder names.
    """

    # Blacklisted dummy or test names that are rejected immediately
    BLACKLISTED_NAMES = {
        "test", "test user", "test account", "tester", "testing",
        "fake", "fake user", "fake name", "fake account",
        "dummy", "dummy user", "dummy account",
        "sample", "sample user", "sample account",
        "john doe", "jane doe", "nobody", "anonymous",
        "admin", "administrator", "root", "hacker",
        "asdf", "asdfgh", "qwerty", "zxcv", "abc", "xyz",
        "foo", "bar", "foo bar", "random", "random user",
        "null", "none", "undefined", "na", "n/a", "no name"
    }

    # Minimum and maximum valid Indian bank account number lengths
    MIN_ACC_LEN = 9
    MAX_ACC_LEN = 18

    @classmethod
    def extract_account_metadata_from_text(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Scans statement header text to extract embedded Account Holder Name and Account Number.
        """
        if not text:
            return None, None

        extracted_name = None
        extracted_acc = None

        # 1. Search for Account Holder Name
        name_patterns = [
            r'(?:account\s*holder(?:\s*name)?|customer\s*name|account\s*name|name\s*of\s*account\s*holder)\s*[:\-]\s*([A-Za-z\s\.\,\'\-]+)',
            r'(?:mr|ms|mrs|dr|smt|shri|m/s)\.?\s+([A-Za-z\s]+)(?:[\r\n,]|$)'
        ]
        for pat in name_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                # Exclude header terms
                if len(candidate) >= 3 and not any(k in candidate.lower() for k in ["statement", "bank", "branch", "ifsc", "limited"]):
                    extracted_name = candidate.title()
                    break

        # 2. Search for Account Number
        acc_patterns = [
            r'(?:account\s*(?:number|no|a/c\s*no|ac\s*no)|a/c|acct\s*no)\s*[:\-\.]?\s*([•\*\dX\s]{0,12}\d{4,18})',
            r'(?:for\s*account|statement\s*for\s*account|savings\s*-\s*)\s*[:\-]?\s*([•\*\dX\s]{0,12}\d{4,18})'
        ]
        for pat in acc_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw_acc = m.group(1).strip().replace(" ", "")
                if len(raw_acc) >= 4:
                    extracted_acc = raw_acc
                    break

        return extracted_name, extracted_acc

    @classmethod
    def validate_account_number(cls, acc_no: str) -> Tuple[bool, str]:
        """
        Validates account number structure, digit length, and rejects fake sequences.
        """
        if not acc_no or not str(acc_no).strip():
            return False, "Account number is missing or empty."

        clean = str(acc_no).strip().replace(" ", "").replace("-", "")

        # Allow partially masked numbers like ••••••••9012 or ****1234
        if re.search(r'^[•\*Xx]+(\d{4,6})$', clean):
            return True, "Valid masked bank account format."

        # Must be strictly numeric
        if not clean.isdigit():
            return False, f"Account number '{clean}' must contain only numeric digits."

        # Length validation for Indian banking accounts
        if len(clean) < cls.MIN_ACC_LEN or len(clean) > cls.MAX_ACC_LEN:
            return False, f"Account number length ({len(clean)} digits) is invalid. Indian bank accounts must be {cls.MIN_ACC_LEN} to {cls.MAX_ACC_LEN} digits."

        # Check for all repeated digits (e.g. 0000000000, 1111111111, 9999999999)
        if len(set(clean)) == 1:
            return False, f"Account number '{clean}' is a fake repeated-digit sequence."

        # Check for sequential patterns (e.g. 1234567890, 0123456789, 9876543210)
        ascending = "01234567890123456789"
        descending = "98765432109876543210"
        if clean in ascending or clean in descending:
            return False, f"Account number '{clean}' is a dummy sequential test pattern."

        # Check for common dummy prefixes with all trailing zeros (e.g. 12300000000)
        if clean.endswith("0000000"):
            return False, f"Account number '{clean}' is an artificial dummy placeholder."

        return True, "Valid authentic account number."

    @classmethod
    def validate_account_holder_name(cls, name: str) -> Tuple[bool, str]:
        """
        Validates the authenticity of the account holder name.
        """
        if not name or not str(name).strip():
            return False, "Account holder name is required."

        clean = str(name).strip()
        lower = clean.lower()

        # Reject blacklisted test names
        if lower in cls.BLACKLISTED_NAMES:
            return False, f"Account holder name '{clean}' is a blacklisted fake/test identity."

        for bl in cls.BLACKLISTED_NAMES:
            if re.search(r'\b' + re.escape(bl) + r'\b', lower):
                return False, f"Account holder name contains prohibited dummy term '{bl}'."

        # Must be at least 3 characters
        if len(clean) < 3:
            return False, "Account holder name is too short (minimum 3 characters required)."

        # Reject names with no letters or mostly numbers/symbols
        letters_only = re.sub(r'[^A-Za-z]', '', clean)
        if len(letters_only) < 3:
            return False, "Account holder name must contain legitimate alphabetical letters."

        # Reject pure gibberish with no vowels (at least 1 vowel required for realistic names)
        if len(clean) >= 4 and not re.search(r'[aeiouAEIOU]', clean):
            return False, f"Account holder name '{clean}' lacks valid linguistic phonetic structure."

        return True, "Valid authentic account holder name."

    @classmethod
    def verify_account(
        cls,
        account_name: Optional[str] = None,
        account_number: Optional[str] = None,
        raw_statement_header: str = "",
        expected_user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive multi-factor account validation.
        Cross-checks provided inputs, extracted header metadata, and authenticity rules.
        """
        # Step 1: If name or account not passed, attempt extraction from statement header
        extracted_name, extracted_acc = cls.extract_account_metadata_from_text(raw_statement_header)

        final_name = account_name or extracted_name or expected_user_name
        final_acc = account_number or extracted_acc

        reasons = []
        is_authentic = True

        # Check Account Number
        if final_acc:
            acc_valid, acc_msg = cls.validate_account_number(final_acc)
            if not acc_valid:
                is_authentic = False
                reasons.append(acc_msg)
        else:
            # If completely missing and not found in headers
            reasons.append("Account number not provided and could not be detected in statement header.")
            acc_valid = False

        # Check Account Holder Name
        if final_name:
            name_valid, name_msg = cls.validate_account_holder_name(final_name)
            if not name_valid:
                is_authentic = False
                reasons.append(name_msg)
        else:
            reasons.append("Account holder name not provided and could not be detected.")
            name_valid = False

        # Step 2: Cross-check between statement embedded name and user name if both exist
        if extracted_name and final_name and extracted_name.lower() != final_name.lower():
            # Check token overlap (e.g. "Arjun Verma" vs "Mr Arjun Verma")
            tokens_extracted = set(re.findall(r'\b[A-Za-z]{3,}\b', extracted_name.lower()))
            tokens_provided = set(re.findall(r'\b[A-Za-z]{3,}\b', final_name.lower()))
            # Remove title words
            titles = {"mr", "mrs", "ms", "dr", "smt", "shri"}
            tokens_extracted -= titles
            tokens_provided -= titles

            if tokens_extracted and tokens_provided and not tokens_extracted.intersection(tokens_provided):
                is_authentic = False
                reasons.append(
                    f"Identity mismatch: Statement belongs to '{extracted_name}', but submitted user name is '{final_name}'."
                )

        # Mask account number for security in report (e.g. ••••••••4821 or 1234••••5678)
        if final_acc and len(final_acc) >= 4:
            clean_digits = re.sub(r'[^\d]', '', final_acc)
            if len(clean_digits) >= 4:
                masked_acc = ("•" * (len(final_acc) - 4)) + clean_digits[-4:]
            else:
                masked_acc = final_acc
        else:
            masked_acc = "UNSPECIFIED"

        return {
            "is_authentic": is_authentic,
            "account_holder_name": final_name or "Unknown",
            "account_number": masked_acc,
            "raw_account_number": final_acc,
            "extracted_from_statement": bool(extracted_name or extracted_acc),
            "reasons": reasons,
            "status": "VERIFIED_AUTHENTIC" if is_authentic else "REJECTED_FAKE_ACCOUNT",
            "message": "Account verified successfully." if is_authentic else f"Account verification failed: {'; '.join(reasons)}"
        }
