import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.category_override import CategoryOverrideModel
from app.models.transaction import TransactionModel

# Default rule-based categorization dictionary for Indian banking narratives
CATEGORY_RULES: Dict[str, List[str]] = {
    "Income": [
        r'\bsalary\b', r'\bpayroll\b', r'\bstipend\b', r'\bdividend\b',
        r'\binterest\s+cr\b', r'\bint\.pd\b', r'\bcashback\b', r'\brefund\b',
        r'\bach\s+cr\b', r'\bcredit\s+interest\b', r'\bpayout\b', r'\bdisbursement\b',
        r'\ballowance\b', r'\binflow\b', r'\bsettlement\b', r'\bremittance\b',
        r'\bfreelance\b', r'\bbonus\b', r'\bclient\s+payment\b', r'\bgig\s+payout\b'
    ],
    "Housing & Rent": [
        r'\brent\b', r'\blandlord\b', r'\bmaintenance\b', r'\bsociety\b',
        r'\bnobroker\b', r'\bmygate\b', r'\bflat\b', r'\bapartment\b',
        r'\bbrokerage\b', r'\bhostel\b', r'\bpg\s+room\b'
    ],
    "Loans & EMI": [
        r'\bemi\b', r'\bloan\b', r'\bbajaj\s+(?:finance|auto\s+finance|finserv)\b',
        r'\bhome\s+loan\b', r'\bcar\s+loan\b', r'\bcredit\s+card\b', r'\bhdfc\s+loan\b',
        r'\bsbi\s+loan\b', r'\bidfc\s+first\b', r'\bcred\b', r'\bmuthoot\b',
        r'\bmanappuram\b', r'\btata\s+capital\b', r'\bl&t\s+finance\b',
        r'\brepay(?:ment)?\b', r'\binstallment\b', r'\bfinance\b'
    ],
    "Investments": [
        r'\bzerodha\b', r'\bgroww\b', r'\bupstox\b', r'\bkuvera\b', r'\bmutual\s+fund\b',
        r'\bsip\b', r'\bmf\b', r'\bppf\b', r'\bnps\b', r'\bindmoney\b', r'\bcoin\b',
        r'\blic\b', r'\buti\b', r'\bsbi\s+mutual\b', r'\bhdfc\s+mutual\b',
        r'\betmoney\b', r'\bsmallcase\b', r'\bequity\b', r'\blife\s+insurance\b'
    ],
    "Education": [
        r'\bexam\s+fee\b', r'\btuition\b', r'\bschool\s+fee\b', r'\bcollege\s+fee\b',
        r'\buniversity\s+fee\b', r'\bxerox\b', r'\bphotocopy\b', r'\btextbook\b',
        r'\bcoursera\b', r'\budemy\b', r'\bedx\b', r'\bcoaching\b',
        r'\bsemester\b', r'\bexam\b', r'\bacademics?\b'
    ],
    "Healthcare": [
        r'\bapollo\b', r'\bpharmeasy\b', r'\b1mg\b', r'\bdr\s+lal\b', r'\bhospital\b',
        r'\bmedical\b', r'\bclinic\b', r'\bpracto\b', r'\bpharmacy\b', r'\bchemist\b',
        r'\bdoctor\b', r'\bdiagnostic\b', r'\bpathology\b', r'\bdental\b'
    ],
    "Subscriptions": [
        r'\bnetflix\b', r'\bspotify\b', r'\bamazon\s+prime\b', r'\bprime\s+video\b',
        r'\bhotstar\b', r'\bdisney\b', r'\byoutube\b', r'\bapple\.com\b', r'\bgoogle\s+play\b',
        r'\bsonyliv\b', r'\bzee5\b', r'\bjiosaavn\b', r'\bgym\b', r'\bcult\.fit\b',
        r'\bchatgpt\b', r'\bopenai\b', r'\bgithub\b', r'\bnotion\b', r'\bstorage\b',
        r'\bgoogle\s+(?:one|storage)\b', r'\bcloud\b', r'\bdropbox\b', r'\bicloud\b'
    ],
    "Utilities & Bills": [
        r'\belectricity\b', r'\bbescom\b', r'\btata\s+power\b', r'\bbroadband\b',
        r'\bairtel\b', r'\bjio\b', r'\bvi\b', r'\bvodafone\b', r'\bact\s+fibernet\b',
        r'\bgas\b', r'\bigas\b', r'\bmgl\b', r'\bwater\b', r'\bmunicipal\b',
        r'\brecharge\b', r'\bdth\b', r'\btata\s+play\b', r'\bpostpaid\b', r'\bbilldesk\b'
    ],
    "Food & Dining": [
        r'\bswiggy\b', r'\bzomato\b', r'\bblinkit\b', r'\bzepto\b', r'\binstamart\b',
        r'\bmcdonald\b', r'\bstarbucks\b', r'\bkfc\b', r'\bdomino\b', r'\bpizza\b',
        r'\bburger\b', r'\brestaurant\b', r'\bcafe\b', r'\bdhaba\b', r'\bbiryani\b',
        r'\beatclub\b', r'\bfaasos\b', r'\bbehrouz\b', r'\bchai\s+point\b', r'\bchaayos\b',
        r'\bblue\s+tokai\b', r'\bsubway\b', r'\bcanteen\b', r'\bchai\b', r'\bbakery\b',
        r'\bsweets\b', r'\bhaldiram\b', r'\bbarbeque\s+nation\b'
    ],
    "Transport": [
        r'\buber\b', r'\bola\b', r'\brapido\b', r'\bmetro\b', r'\bpetrol\b',
        r'\bfuel\b', r'\bhpcl\b', r'\bbpcl\b', r'\biocl\b', r'\bshell\b',
        r'\bfastag\b', r'\bauto\s+(?:rickshaw|fare|ride|meter|taxi)\b', r'\btoll\b',
        r'\birctc\b', r'\bindigo\b', r'\bair\s+india\b', r'\bcleartrip\b',
        r'\bmakemytrip\b', r'\boverhaul\b', r'\brepair\b', r'\bmechanic\b',
        r'\bgarage\b', r'\bpuncture\b', r'\btyre\b', r'\bparking\b', r'\bcab\b'
    ],
    "Shopping": [
        r'\bamazon\b', r'\bflipkart\b', r'\bmyntra\b', r'\bmeesho\b', r'\bzara\b',
        r'\bnykaa\b', r'\bajio\b', r'\btata\s+cliq\b', r'\bh&m\b', r'\breliance\s+retail\b',
        r'\bdecathlon\b', r'\buniqlo\b', r'\blifestyl\b', r'\bshoppers\s+stop\b',
        r'\btanishq\b', r'\bjeweller(?:y)?\b', r'\bjewelry\b', r'\bclothing\b',
        r'\bretail\b', r'\bmart\b', r'\bbazaar\b', r'\bsupermarket\b', r'\bgrocery\b'
    ],
    "Transfers": [
        r'\bp2p\b', r'\bself\s+transfer\b', r'\btransfer\s+to\b', r'\bneft\s+to\b',
        r'\bimps\s+to\b', r'\bfunds?\s+transfer\b', r'\bacc\s+transfer\b', r'\btransfer\b'
    ]
}

# Gig platform keywords where inflows (credits) represent worker income
GIG_PLATFORMS = {"swiggy", "zomato", "uber", "zepto", "blinkit", "porter", "dunzo", "urban company", "rapido"}

# Canonical merchant mapping dictionary
CANONICAL_MERCHANTS: Dict[str, str] = {
    "SWIGGY BUNDL": "SWIGGY",
    "SWIGGY BANGALORE": "SWIGGY",
    "SWIGGY INSTAMART": "SWIGGY",
    "ZOMATO MEDIA": "ZOMATO",
    "ZOMATO PAY": "ZOMATO",
    "UBER INDIA": "UBER",
    "UBER TRIP": "UBER",
    "RELIANCE JIO": "JIO",
    "JIO PREPAID": "JIO",
    "AIRTEL BROADBAND": "AIRTEL",
    "AIRTEL FIBER": "AIRTEL",
    "IRCTC WEB": "IRCTC",
    "IRCTC ETICKET": "IRCTC",
    "BAJAJ AUTO": "BAJAJ FINANCE",
    "BAJAJ AUTO FINANCE": "BAJAJ FINANCE",
    "BAJAJ FINSERV": "BAJAJ FINANCE",
    "LIC OF INDIA": "LIC",
    "LIFE INSURANCE": "LIC",
    "GOOGLE STORAGE": "GOOGLE ONE",
    "GOOGLE ONE": "GOOGLE ONE",
    "SPOTIFY INDIA": "SPOTIFY",
    "NETFLIX ENTERTAINMENT": "NETFLIX",
    "CULT.FIT GYM": "CULT.FIT",
    "TANISHQ JEWELLERY": "TANISHQ",
    "HPCL PETROL": "HPCL",
    "BPCL PETROL": "BPCL",
    "IOCL PETROL": "IOCL"
}

class TransactionCategorizer:
    """
    Intelligent categorization engine that combines:
      1. User-specific custom overrides (highest priority)
      2. Directional awareness (Inflows / Credits vs Outflows / Debits)
      3. Regular-expression keyword rules for Indian merchants
      4. Normalized merchant dictionary
      5. Confidence scoring with 'Uncategorized – review' fallback
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
            # Strip trailing payment handles (e.g. paytm@axis, @okaxis)
            merchant_candidate = re.sub(r'[/@].*$', '', merchant_candidate).strip()
            if not re.match(r'^[0-9]+$', merchant_candidate) and len(merchant_candidate) >= 3:
                norm = merchant_candidate.upper()
                for prefix, canonical in CANONICAL_MERCHANTS.items():
                    if prefix in norm:
                        return canonical
                return norm

        # Handle POS pattern: POS XXXXX MERCHANT NAME CITY
        pos_match = re.search(r'pos\s+(?:[\w\d]+\s+)?([a-zA-Z\s]{3,25})', clean, re.IGNORECASE)
        if pos_match:
            norm = pos_match.group(1).strip().upper()
            for prefix, canonical in CANONICAL_MERCHANTS.items():
                if prefix in norm:
                    return canonical
            return norm

        # Handle NEFT/IMPS: NEFT-XXXX-MERCHANT
        neft_match = re.search(r'(?:neft|imps)[/-](?:[\w\d]+[/-])?([a-zA-Z\s]{3,25})', clean, re.IGNORECASE)
        if neft_match:
            norm = neft_match.group(1).strip().upper()
            for prefix, canonical in CANONICAL_MERCHANTS.items():
                if prefix in norm:
                    return canonical
            return norm

        # Fallback: take first 2-3 alphanumeric words, stripping pure numbers
        words = [w for w in re.split(r'[\s/_/.-]+', clean) if w and not re.match(r'^[0-9]+$', w)]
        if words:
            candidate = " ".join(words[:2]).upper()
            for prefix, canonical in CANONICAL_MERCHANTS.items():
                if prefix in candidate:
                    return canonical
            return candidate

        return clean[:20].upper()

    @classmethod
    def categorize_with_confidence(
        cls,
        description: str,
        credit: float = 0.0,
        debit: float = 0.0,
        user_overrides: Optional[Dict[str, str]] = None
    ) -> Tuple[str, float]:
        """
        Determines the category and confidence score for a transaction.
        Returns:
            (category_name, confidence_score) where confidence_score in [0.0, 1.0].
            Falls back to ('Uncategorized – review', score) if confidence is below threshold.
        """
        desc_lower = description.lower()
        merchant = cls.extract_normalized_merchant(description).upper()

        # 1. User overrides (highest priority, 1.0 confidence)
        if user_overrides:
            for pattern, cat in user_overrides.items():
                if pattern.upper() in merchant or pattern.lower() in desc_lower:
                    return (cat, 1.0)

        # 2. Inflow / Credit Directional Logic
        if credit > 0:
            # Check if this credit is a gig platform payout (e.g. Swiggy/Zomato/Uber partner inflow)
            if any(gp in desc_lower for gp in GIG_PLATFORMS):
                return ("Income", 0.98)

            # Check explicit income patterns
            for pattern in CATEGORY_RULES["Income"]:
                if re.search(pattern, desc_lower):
                    return ("Income", 0.95)

            # Check for refund / reversal
            if any(w in desc_lower for w in ["refund", "cashback", "reversal", "reimburse"]):
                return ("Income", 0.90)

            # General credit fallback
            return ("Income", 0.85)

        # 3. Expense / Debit Directional Logic
        # Prioritized check: Housing, Loans/EMI, Investments first to avoid false generic matches
        priority_order = [
            "Housing & Rent",
            "Loans & EMI",
            "Investments",
            "Healthcare",
            "Subscriptions",
            "Utilities & Bills",
            "Food & Dining",
            "Education",
            "Transport",
            "Shopping",
            "Transfers"
        ]

        for cat in priority_order:
            patterns = CATEGORY_RULES[cat]
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    return (cat, 0.92)

        # 4. Fallback for unrecognized descriptions: local offline char n-gram ML classifier
        from app.services.fallback_classifier import FallbackClassifier
        ml_cat, ml_conf = FallbackClassifier.predict(description)
        if ml_cat and ml_conf >= 0.25:
            return (ml_cat, round(ml_conf, 2))

        return ("Uncategorized – review", 0.25)

    @classmethod
    def categorize(
        cls,
        description: str,
        credit: float = 0.0,
        debit: float = 0.0,
        user_overrides: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Determines the category for a transaction (backward-compatible string output).
        Maps 'Uncategorized – review' to 'Uncategorized' for existing schema consumers.
        """
        cat, conf = cls.categorize_with_confidence(
            description,
            credit=credit,
            debit=debit,
            user_overrides=user_overrides
        )
        if cat == "Uncategorized – review":
            return "Uncategorized"
        return cat

    @classmethod
    def apply_to_transactions(cls, transactions: List[TransactionModel], db: Session) -> None:
        """
        Applies rules and saved overrides in database to all transactions.
        """
        overrides = {o.merchant_pattern: o.category for o in db.query(CategoryOverrideModel).all()}

        for tx in transactions:
            if not tx.user_overridden:
                tx.normalized_merchant = cls.extract_normalized_merchant(tx.description)
                cat, _ = cls.categorize_with_confidence(
                    tx.description,
                    credit=tx.credit,
                    debit=tx.debit,
                    user_overrides=overrides
                )
                tx.category = "Uncategorized" if cat == "Uncategorized – review" else cat
        db.commit()
