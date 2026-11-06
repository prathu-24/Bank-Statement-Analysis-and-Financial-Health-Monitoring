import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.category_override import CategoryOverrideModel
from app.models.transaction import TransactionModel

# Default rule-based categorization dictionary for Indian bank narratives
CATEGORY_RULES: Dict[str, List[str]] = {
    "Income": [
        r'\bsalary\b', r'\bpayroll\b', r'\bstipend\b', r'\bdividend\b',
        r'\binterest\s+cr\b', r'\bint\.pd\b', r'\bcashback\b', r'\brefund\b',
        r'\bach\s+cr\b', r'\bcredit\s+interest\b'
    ],
    "Food & Dining": [
        r'\bswiggy\b', r'\bzomato\b', r'\bblinkit\b', r'\bzepto\b', r'\binstamart\b',
        r'\bmcdonald\b', r'\bstarbucks\b', r'\bkfc\b', r'\bdomino\b', r'\bpizza\b',
        r'\bburger\b', r'\brestaurant\b', r'\bcafe\b', r'\bdhaba\b', r'\bbiryani\b',
        r'\beatclub\b', r'\bfaasos\b', r'\bbehrouz\b', r'\bchai\s+point\b'
    ],
    "Transport": [
        r'\buber\b', r'\bola\b', r'\brapido\b', r'\bmetro\b', r'\bpetrol\b',
        r'\bfuel\b', r'\bhpcl\b', r'\bbpcl\b', r'\biocl\b', r'\bshell\b',
        r'\bfastag\b', r'\bauto\b', r'\btoll\b', r'\birctc\b', r'\bindigo\b',
        r'\bair\s+india\b', r'\bcleartrip\b', r'\bmakemytrip\b'
    ],
    "Subscriptions": [
        r'\bnetflix\b', r'\bspotify\b', r'\bamazon\s+prime\b', r'\bprime\s+video\b',
        r'\bhotstar\b', r'\byoutube\b', r'\bapple\.com\b', r'\bgoogle\s+play\b',
        r'\bsonyliv\b', r'\bzee5\b', r'\bjiosaavn\b', r'\bgym\b', r'\bcult\.fit\b',
        r'\bchatgpt\b', r'\bopenai\b', r'\bgithub\b', r'\bnotion\b'
    ],
    "Shopping": [
        r'\bamazon\b', r'\bflipkart\b', r'\bmyntra\b', r'\bmeesho\b', r'\bzara\b',
        r'\bnykaa\b', r'\bajio\b', r'\btata\s+cliq\b', r'\bh&m\b', r'\breliance\s+retail\b',
        r'\bdecathlon\b', r'\buniqlo\b', r'\blifestyl\b', r'\bshoppers\s+stop\b'
    ],
    "Utilities & Bills": [
        r'\belectricity\b', r'\bbescom\b', r'\btata\s+power\b', r'\bbroadband\b',
        r'\bairtel\b', r'\bjio\b', r'\bvi\b', r'\bvodafone\b', r'\bact\s+fibernet\b',
        r'\bgas\b', r'\bigas\b', r'\bmgl\b', r'\bwater\b', r'\bmunicipal\b',
        r'\brecharge\b', r'\bdth\b', r'\btata\s+play\b'
    ],
    "Housing & Rent": [
        r'\brent\b', r'\blandlord\b', r'\bmaintenance\b', r'\bsociety\b',
        r'\bnobroker\b', r'\bmygate\b', r'\bflat\b', r'\bapartment\b'
    ],
    "Loans & EMI": [
        r'\bemi\b', r'\bloan\b', r'\bbajaj\s+finserv\b', r'\bhome\s+loan\b',
        r'\bcar\s+loan\b', r'\bcredit\s+card\b', r'\bhdfc\s+loan\b', r'\bsbi\s+loan\b',
        r'\bidfc\s+first\b', r'\bcred\b'
    ],
    "Investments": [
        r'\bzerodha\b', r'\bgroww\b', r'\bupstox\b', r'\bkuvera\b', r'\bmutual\s+fund\b',
        r'\bsip\b', r'\bmf\b', r'\bppf\b', r'\bnps\b', r'\bindmoney\b', r'\bcoin\b'
    ],
    "Healthcare": [
        r'\bapollo\b', r'\bpharmeasy\b', r'\b1mg\b', r'\bdr\s+lal\b', r'\bhospital\b',
        r'\bmedical\b', r'\bclinic\b', r'\bpracto\b', r'\bpharmacy\b', r'\bchemist\b'
    ],
    "Transfers": [
        r'\bupi\b', r'\bimps\b', r'\bneft\b', r'\brtgs\b', r'\bp2p\b', r'\btransfer\b'
    ]
}

class TransactionCategorizer:
    """
    Intelligent categorization engine that combines:
      1. User-specific custom overrides (highest priority)
      2. Regular-expression keyword rules for Indian merchants
      3. Transaction direction heuristics (credit vs debit)
      4. Safe fallback to 'Uncategorized' for unknown merchants
    """

    @classmethod
    def extract_normalized_merchant(cls, description: str) -> str:
        """
        Strips banking noise (UPI prefixes, reference codes, dates, account numbers)
        to extract the core merchant or party name.
        Example: 'UPI/324213401/ZOMATO/paytm@axis/Ref991' -> 'ZOMATO'
        """
        if not description:
            return "UNKNOWN"

        clean = description.strip()

        # Handle UPI pattern: UPI/Ref/Merchant/... or UPI-Merchant-Ref
        upi_match = re.search(r'upi[/-](?:[\w\d]+[/-])?([a-zA-Z\s0-9]{3,25})[/-]?', clean, re.IGNORECASE)
        if upi_match:
            merchant_candidate = upi_match.group(1).strip()
            # If candidate isn't just digits/hex, use it
            if not re.match(r'^[0-9]+$', merchant_candidate):
                return merchant_candidate.upper()

        # Handle POS pattern: POS XXXXX MERCHANT NAME CITY
        pos_match = re.search(r'pos\s+(?:[\w\d]+\s+)?([a-zA-Z\s]{3,25})', clean, re.IGNORECASE)
        if pos_match:
            return pos_match.group(1).strip().upper()

        # Handle NEFT/IMPS: NEFT-XXXX-MERCHANT
        neft_match = re.search(r'(?:neft|imps)[/-](?:[\w\d]+[/-])?([a-zA-Z\s]{3,25})', clean, re.IGNORECASE)
        if neft_match:
            return neft_match.group(1).strip().upper()

        # Fallback: take first 2-3 alphanumeric words, stripping pure numbers
        words = [w for w in re.split(r'[\s/_/.-]+', clean) if w and not re.match(r'^[0-9]+$', w)]
        if words:
            return " ".join(words[:2]).upper()

        return clean[:20].upper()

    @classmethod
    def categorize(
        cls,
        description: str,
        credit: float = 0.0,
        debit: float = 0.0,
        user_overrides: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Determines the category for a transaction based on description, direction, and overrides.
        """
        desc_lower = description.lower()
        merchant = cls.extract_normalized_merchant(description).upper()

        # 1. User overrides (highest priority)
        if user_overrides:
            for pattern, cat in user_overrides.items():
                if pattern.upper() in merchant or pattern.lower() in desc_lower:
                    return cat

        # 2. Check Income rules if money credited
        if credit > 0:
            for pattern in CATEGORY_RULES["Income"]:
                if re.search(pattern, desc_lower):
                    return "Income"

        # 3. Check Expense rules
        for category, patterns in CATEGORY_RULES.items():
            if category == "Income" and debit > 0:
                continue
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    return category

        # 4. If credit with no other match, default to Income if significant or general Credit
        if credit > 0 and debit == 0:
            if "salary" in desc_lower or "payroll" in desc_lower:
                return "Income"
            return "Income"

        # 5. Safe fallback
        return "Uncategorized"

    @classmethod
    def apply_to_transactions(cls, transactions: List[TransactionModel], db: Session) -> None:
        """
        Applies rules and saved overrides in database to all transactions.
        """
        overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}

        for tx in transactions:
            if not tx.user_overridden:
                tx.normalized_merchant = cls.extract_normalized_merchant(tx.description)
                tx.category = cls.categorize(
                    tx.description,
                    credit=tx.credit,
                    debit=tx.debit,
                    user_overrides=overrides
                )
        db.commit()

