import os
import glob
import json
import hashlib
from datetime import datetime, timezone
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT_DIR, "demo_data")
MODELS_DATA_DIR = os.path.join(ROOT_DIR, "backend", "app", "models_data")
os.makedirs(MODELS_DATA_DIR, exist_ok=True)

def get_forbidden_descriptions() -> set:
    forbidden = set()
    for f in glob.glob(os.path.join(DEMO_DIR, "*.csv")):
        try:
            df = pd.read_csv(f)
            for col in ["Description", "Narration", "Transaction Description"]:
                if col in df.columns:
                    for d in df[col].dropna():
                        s = str(d).strip().upper()
                        if s:
                            forbidden.add(s)
        except Exception:
            pass

    for f in glob.glob(os.path.join(DEMO_DIR, "*.json")):
        try:
            with open(f, encoding="utf-8") as jf:
                data = json.load(jf)
                if "true_categories" in data:
                    for d in data["true_categories"]:
                        forbidden.add(str(d).strip().upper())
                if "planted_events" in data:
                    for ev in data["planted_events"]:
                        if "description" in ev:
                            forbidden.add(str(ev["description"]).strip().upper())
        except Exception:
            pass
    return forbidden

# Diverse disjoint synthetic bank narratives across India
# Merchants, keywords, and phrasing templates constructed to be disjoint from all demo_data files
RAW_SYNTHETIC_TEMPLATES = {
    "Food & Dining": [
        "UPI/BIRYANI BY KILO GURGAON/LUNCH ORDER",
        "UPI/PUNJAB GRILL SAKET/FAMILY DINNER",
        "UPI/MAINLAND CHINA KORAMANGALA/FOOD",
        "UPI/PARAS SWEETS JAIPUR/MITHAI BOX",
        "POS 8821 KARACHI BAKERY HYDERABAD",
        "UPI/SOCIAL OFFLINE HAUZ KHAS/CAFE SNACKS",
        "UPI/MOCAMBO RESTAURANT PARK STREET/LUNCH",
        "POS 3412 COPPER CHIMNEY WORLI",
        "UPI/PETER CAT KOLKATA/CHELLO KEBAB",
        "UPI/SARAVANA BHAVAN JANPATH/SOUTH INDIAN BREAKFAST",
        "UPI/MURUGAN IDLI SHOP MADURAI/TIFFIN",
        "UPI/GAYLORD RESTAURANT CHURCHGATE/BAKERY",
        "POS 9942 KAVERI VEG THALI MYSORE",
        "UPI/CHOWMAN CHINESE INDIRANAGAR/FOOD ORDER",
        "UPI/FLURYS TEAROOM KOLKATA/PASTRY CAFE",
        "POS 5519 BIKANERVALA CHANDNI CHOWK/SWEETS",
        "UPI/BADEMIYAN COLABA/KABAB DINNER",
        "UPI/CREAM STONE ICE CREAM BANJARA HILLS",
        "POS 1129 MADRAS CAFE MATUNGA/DOSA FILTER COFFEE",
        "UPI/KUREMAL MOHAN LAL KULFI CHAWRI BAZAR",
        "UPI/PARASHAR FOODS CONNAUGHT PLACE/RAJMA CHAWAL",
        "UPI/VAISHALI RESTAURANT FC ROAD PUNE/COLD COFFEE",
        "POS 7731 WOKING MAMA PAN ASIAN/MEAL",
        "UPI/SUBWAY SANDWICH AIRPORT T3/MEAL COMBO",
        "UPI/PABRAI FRESH NATURE ICECREAM/SCOOP",
        "POS 6620 BARBEQUE NATION GOMTI NAGAR/DINNER",
        "UPI/THE YELLOW CHILLI NOIDA/NORTH INDIAN",
        "UPI/MUGHLAI JUNCTION ALIGARH/CHICKEN ROLL",
        "POS 4490 PARAGON RESTAURANT KOZHIKODE/BIRYANI",
        "UPI/SHREE THAKER BHOJANALAY KALBADEVI/GUJARATI THALI",
        "UPI/MAMA GOTO KHAN MARKET/DIMSUM LUNCH",
        "POS 1209 SHIV SAGAR JUHU/PAV BHAJI",
        "UPI/CORNER HOUSE ICE CREAM LAVELLE RD/DESSERT",
        "UPI/GOPAL SWEETS CHANDIGARH/SNACKS",
        "POS 9901 CHHAPPAN BHOG LUCKNOW/SWEETS"
    ],
    "Groceries": [
        "UPI/SPENCERS RETAIL SUPERMARKET/DAILY PROVISIONS",
        "POS 3321 SPAR HYPERMARKET KUKATPALLY/GROCERIES",
        "UPI/STAR BAZAAR ANDHERI WEST/RICE DAL OIL",
        "UPI/EASYDAY CLUB STORE LUDHIANA/GROCERY BASKET",
        "POS 5521 MORE SUPERMARKET BELLANDUR/WEEKLY VEGGIES",
        "UPI/RATNADEEP SUPERMARKET JUBILEE HILLS/PROVISIONS",
        "UPI/NILGIRIS SUPERSTORE INDIRANAGAR/DAIRY MILK",
        "POS 7781 HERITAGE FRESH STORE BANJARA HILLS",
        "UPI/DORABJEES GOURMET STORE CAMP PUNE/IMPORT FOOD",
        "UPI/KUMAR SUPER STORE DEHRADUN/STAPLES FLOUR",
        "POS 4410 RELIANCE FRESH VEGETABLES/TOMATO ONION",
        "UPI/VILLAGE GROCERY MART SURAT/GRAINS PULSES",
        "UPI/APNA BAZAAR COOPERATIVE STORE DADAR",
        "POS 9931 MODERN BAZAAR VASANT VIHAR/ORGANIC DAL",
        "UPI/SARAVANA STORES CHENNAI/PROVISION RETAIL",
        "UPI/FAMILY SUPERMART COIMBATORE/KITCHEN STAPLES",
        "POS 1144 WHOLE FOODS ORGANIC STORE AHMEDABAD",
        "UPI/GREEN BASKET FARM FRESH VEGETABLES/VEG ORDER",
        "UPI/NAMDHARI FRESH GREEN GROCER/FRUITS VEGGIES",
        "POS 6629 DAILY NEEDS PROVISION STORE CHANDIGARH"
    ],
    "Shopping": [
        "UPI/ZARA PHOENIX PALLADIUM/SUMMER SHIRTS",
        "POS 8829 H&M SELECT CITYWALK/DENIM JEANS",
        "UPI/LIFESTYLE INTERNATIONAL STORE/FOOTWEAR",
        "UPI/SHOPPERS STOP MALAD/COSMETICS PERFUME",
        "POS 4419 PANTALOONS FASHION RETAIL/KURTA SET",
        "UPI/FABINDIA OVERSEAS ETHNIC WEAR/COTTON DRESS",
        "POS 2209 RELIANCE TRENDS APPAREL/T-SHIRTS",
        "UPI/WOODLAND FOOTWEAR LEATHER BOOTS/SHOES",
        "UPI/BATA INDIA LTD FOOTWEAR/FORMAL SHOES",
        "POS 7712 METRO SHOES HIGH STREET/SANDALS",
        "UPI/RAYMOND APPAREL STORE/SUITING FABRIC",
        "UPI/MANYAVAR MOHEY ETHNIC WEAR/SHERWANI",
        "POS 3390 CROCS RETAIL FOOTWEAR/CLOGS",
        "UPI/TITAN WATCHES WORLD SHOWROOM/WRISTWATCH",
        "UPI/CARAT LANE JEWELLERY TANISHQ/GOLD RING",
        "POS 9920 BLUESTONE JEWELLERY STORE/SILVER PENDANT",
        "UPI/LENOVO EXCLUSIVE LAPTOP STORE/ACCESORIES",
        "UPI/CHUMBAK DESIGN SOUVENIR STORE/GIFT ITEMS",
        "POS 5501 HAMLEYS TOY RETAIL SHOP/BOARD GAME",
        "UPI/ARCHIES GALLERY CARDS/BIRTHDAY GIFTS"
    ],
    "Transport": [
        "UPI/UBER INDIA SYSTEMS PVT LTD/CAB RIDE AIRPORT",
        "UPI/OLA CABS FLEET TECHNOLOGIES/AUTO COMMUTE",
        "UPI/RAPIDO BIKE TAXI ROPOSO/OFFICE TRAVEL",
        "POS 3381 BHARAT PETROLEUM PUMP BANDRA/PETROL FILL",
        "POS 4492 HINDUSTAN PETROLEUM CORPORATION/DIESEL",
        "UPI/INDIAN OIL RETAIL OUTLET NOIDA/FUEL REFILL",
        "UPI/MAHARASHTRA STATE ROAD TRANSPORT/MSRTC BUS",
        "UPI/KSRTC ONLINE BUS TICKET BOOKING/TRAVEL",
        "POS 8820 DELHI METRO RAIL CORPORATION/METRO SMART CARD",
        "UPI/MUMBAI METRO LINE 1 CHARGE/METRO COMMUTE",
        "UPI/BANGALORE METRO RAIL BMRCL/SMARTCARD RECHARGE",
        "UPI/CHENNAI METRO RAIL CMRL/TRANSIT TOKEN",
        "POS 5510 SHELL PETROL PUMP WHITEFIELD/SUPER DIESEL",
        "UPI/JIO-BP FUEL SERVICE STATION/MOTORCYCLE FUEL",
        "UPI/FASTAG HIGHWAY TOLL PLAZA IHMCL/TOLL DEDUCTION",
        "UPI/IRCTC INDIAN RAILWAYS/TRAIN RESERVATION TICKET",
        "POS 9921 NAYARA ENERGY FUEL STATION/PETROL EXPENSE",
        "UPI/MERU CABS FLEET SERVICE/AIRPORT DROP",
        "UPI/ZIGWHEELS AUTO WORKSHOP SERVICE/CAR REPAIR",
        "UPI/TIRE EMPIRE CAR WHEEL ALIGNMENT/TYRE ROTATION"
    ],
    "Healthcare": [
        "UPI/MANIPAL HOSPITAL WHITEFIELD/DOCTOR CONSULTATION",
        "UPI/FORTIS MEMORIAL RESEARCH INSTITUTE/OPD FEE",
        "POS 3319 MEDANTA THE MEDICITY GURGAON/CONSULTING",
        "UPI/NARAYANA HEALTH CITY BANGALORE/CARDIAC CHECK",
        "UPI/COLUMBIA ASIA HOSPITAL YESHWANTHPUR/MEDICINES",
        "POS 7721 DR LAL PATHLABS DIAGNOSTIC/BLOOD PROFILE",
        "UPI/METROPOLIS HEALTHCARE LAB/URINE TEST REPORT",
        "UPI/THYROCARE TECHNOLOGIES LTD/THYROID PANEL",
        "POS 9912 SRL DIAGNOSTICS PATHOLOGY CLINIC/HEALTH CHECK",
        "UPI/NETMEDS MARKETPLACE PHARMACY/PRESCRIPTION DRUGS",
        "UPI/TATA 1MG HEALTHCARE PHARMACY/MEDICINE DISPATCH",
        "POS 4411 PHARMEASY ONLINE MEDICINE BILL/PRESCRIPTION",
        "UPI/GUARDIAN PHARMACY RETAIL STORE/FIRST AID",
        "UPI/CLOVE DENTAL CLINIC SOUTH EXTENSION/DENTAL XRAY",
        "POS 2201 SABKA DENTIST CLINIC BORIVALI/ROOT CANAL",
        "UPI/DR BATRA HOMEOPATHY CLINIC/HAIR CONSULTATION",
        "UPI/EYE-Q SUPER SPECIALTY EYE HOSPITAL/CATARACT OPD",
        "POS 8830 SHANKARA EYE HOSPITAL BANGALORE/GLASSES",
        "UPI/WELLNESS FOREVER MEDICHEM PHARMACY/STORE BILL",
        "UPI/NOBLE PHARMACY CHEMIDRUG/PRESCRIPTION REFILL"
    ],
    "Education": [
        "UPI/ALLEN CAREER INSTITUTE KOTA/TEST SERIES FEE",
        "UPI/FIITJEE SOUTH DELHI/COACHING STUDY MATERIAL",
        "POS 4401 AAKASH EDUCATIONAL SERVICES/MEDICAL ENTRANCE",
        "UPI/RESONANCE EDUVENTURES KOTA/EXAM BATCH FEE",
        "UPI/BRITISH COUNCIL ENGLISH COURSE/IELTS EXAM FEE",
        "UPI/CAMBRIDGE UNIVERSITY PRESS/TEXTBOOKS PURCHASE",
        "POS 9918 OXFORD UNIVERSITY PRESS/ACADEMIC DICTIONARY",
        "UPI/NATIONAL TESTING AGENCY NTA/NEET APPLICATION FEE",
        "UPI/UNION PUBLIC SERVICE COMMISSION UPSC/EXAM FORM",
        "UPI/MAHARASHTRA STATE BOARD/SSC EXAM REGISTRATION",
        "POS 3320 SAPNA BOOK HOUSE GANDHINAGAR/STUDY BOOKS",
        "UPI/HIGGINBOTHAMS BOOKSTORE CHENNAI/ENGINEERING BOOKS",
        "UPI/STRAND BOOK STALL FORT MUMBAI/LIBRARY NOVELS",
        "UPI/XEROX COPY CENTER NORTH CAMPUS/LECTURE PHOTOCOPY",
        "UPI/STUDENT PHOTOSTAT SHOP IIT DELHI/NOTES BINDING",
        "POS 6619 COURSERA INC ONLINE/DATA SCIENCE SPECIALIZATION",
        "UPI/UDEMY ONLINE SYSTEM DESIGN/COURSE ENROLLMENT",
        "UPI/EDX ONLINE HARVARD CS50/VERIFIED CERTIFICATE",
        "UPI/PLURALSIGHT ANNUAL TECH/DEVELOPER SUBSCRIPTION",
        "UPI/SWAYAM NPTEL ONLINE CERTIFICATION/GOVT EXAM"
    ],
    "Utilities & Bills": [
        "UPI/TATA POWER DELHI DISTRIBUTION TPDDL/ELEC BILL",
        "UPI/BSES RAJDHANI POWER LIMITED BRPL/ELECTRICITY",
        "UPI/BESCOM BANGALORE ELECTRICITY/BILL PAYMENT",
        "UPI/MAHAVITARAN MSEDCL MAHARASHTRA/POWER BILL",
        "POS 4418 ADANI ELECTRICITY MUMBAI LIMITED/UTILITY",
        "UPI/INDRAPRASTHA GAS LIMITED IGL/PIPED COOKING GAS",
        "UPI/MAHANAGAR GAS LIMITED MGL/PNG GAS UTILITY",
        "UPI/GUJARAT GAS LIMITED/DOMESTIC GAS BILLPAY",
        "UPI/DELHI JAL BOARD DJB/WATER SUPPLY TARIFF",
        "UPI/BANGALORE WATER BWSSB/WATER METER CHARGE",
        "UPI/BHARTI AIRTEL LIMITED/POSTPAID FIBER BROADBAND",
        "UPI/JIO FIBER BROADBAND/MONTHLY INTERNET PLAN",
        "POS 9922 ACT FIBERNET BEAM TELECOM/BROADBAND RENEWAL",
        "UPI/TATA PLAY LIMITED/DTH SATELLITE RECHARGE",
        "UPI/DISH TV DTH SERVICES INDIA/TELEVISION PACK",
        "UPI/VODAFONE IDEA VI POSTPAID/MOBILE PHONE BILL"
    ],
    "Subscriptions": [
        "UPI/NETFLIX ENTERTAINMENT SERVICES/STREAMING PLAN",
        "UPI/AMAZON PRIME VIDEO ANNUAL MEMBERSHIP/DIGITAL",
        "POS 3302 DISNEY PLUS HOTSTAR/VIP ANNUAL STREAMING",
        "UPI/SPOTIFY INDIA MUSIC SUBSCRIPTION/INDIVIDUAL DUO",
        "UPI/APPLE.COM/BILL ICLOUD STORAGE 50GB/CLOUD BACKUP",
        "UPI/GOOGLE STORAGE ONE DRIVE/EXPANDED 100GB CLOUD",
        "UPI/YOUTUBE PREMIUM FAMILY PLAN/AD FREE STREAMING",
        "POS 7719 SONYLIV PREMIUM ANNUAL PLAN/SONY LIV DIGITAL",
        "UPI/ZEE5 ENTERTAINMENT DIGITAL VIP/SUBSCRIPTION",
        "UPI/JIOSAAVN PRO MUSIC SUBSCRIPTION/HQ AUDIO",
        "UPI/GAANA PLUS TIMES INTERNET/STREAMING PASS",
        "POS 8812 CULT.FIT FITNESS PASS/GYM MEMBERSHIP RENEWAL",
        "UPI/GOLDS GYM ANNUAL MEMBERSHIP/HEALTH PASS",
        "UPI/OPENAI CHATGPT PLUS/MONTHLY AI SUBSCRIPTION",
        "UPI/GITHUB DEVELOPER PRO ACCOUNT/CODING TOOL"
    ],
    "Housing & Rent": [
        "TRANSFER TO MR SHARMA LANDLORD/MONTHLY FLAT RENT",
        "NEFT-CR-SMT KAMALA DEVI/APARTMENT RENT FOR MAY",
        "UPI/MYGATE SOCIETY MAINTENANCE/BUILDING DUES",
        "UPI/NOBROKER APARTMENT MAINTENANCE CHARGES",
        "UPI/PURVA HIGHLAND FLAT OWNERS ASSOCIATION/MAINT",
        "UPI/PRESTIGE SHANTINIKETAN RESIDENTS/SOCIETY CHARGES",
        "TRANSFER TO ANANDIBAI PG HOSTEL/ROOM SHARING RENT",
        "UPI/STAYABODE CO-LIVING SPACES/MONTHLY RENT",
        "UPI/ZOLO STAYS CO-LIVING/STUDENT ACCOMMODATION RENT"
    ],
    "Loans & EMI": [
        "ACH DEBIT-BAJAJ FINANCE LIMITED/CONSUMER DURABLE EMI",
        "ACH DEBIT-HDFC BANK HOME LOAN/MONTHLY MORTGAGE",
        "ACH DEBIT-ICICI BANK CAR LOAN/AUTO EMI DEBIT",
        "ACH DEBIT-SBI HOUSING LOAN INSTALLMENT/REPAYMENT",
        "UPI/CRED CLUB CREDIT CARD PAYMENT/BILL CLEARANCE",
        "UPI/IDFC FIRST BANK PERSONAL LOAN/MONTHLY INSTALMENT",
        "ACH DEBIT-TATA CAPITAL FINANCIAL/BUSINESS LOAN",
        "UPI/MUTHOOT FINANCE GOLD LOAN/INTEREST PAYMENT",
        "ACH DEBIT-L&T FINANCE HOLDINGS/EQUIPMENT EMI",
        "UPI/MANAPPURAM JEWELLERY LOAN/LOAN SETTLEMENT"
    ],
    "Investments": [
        "ACH DEBIT-ZERODHA BROKING LTD/EQUITY SIP TRADING",
        "UPI/GROWW NEXTBILLION TECHNOLOGY/MUTUAL FUND SIP",
        "ACH DEBIT-UPSTOX RKSV SECURITIES/MONTHLY STOCKS",
        "UPI/INDMONEY PRIVATE LIMITED/US STOCKS INVESTMENT",
        "ACH DEBIT-SBI MUTUAL FUND SCHEME/GROWTH DIRECT SIP",
        "ACH DEBIT-HDFC ASSET MANAGEMENT/EQUITY MUTUAL FUND",
        "ACH DEBIT-NIPPON INDIA MUTUAL FUND/LARGE CAP DIRECT",
        "UPI/ETMONEY TIMES INTERNET/TAX SAVER ELSS FUND",
        "UPI/LIFE INSURANCE CORP OF INDIA LIC/PREMIUM PAYMENT",
        "ACH DEBIT-HDFC LIFE INSURANCE CO/TERM LIFE PREMIUM",
        "UPI/SBI LIFE ASSURANCE/ANNUAL LIFE POLICY DUES"
    ],
    "Income": [
        "NEFT-CR-INFOSYS LIMITED/SALARY CREDIT FOR MONTH",
        "NEFT-CR-TCS TATA CONSULTANCY/MONTHLY PAYROLL DEPOSIT",
        "NEFT-CR-WIPRO ENTERPRISES/NET REMUNERATION INFLOW",
        "NEFT-CR-COGNIZANT TECHNOLOGY/MONTHLY PAYROLL CR",
        "ACH CREDIT-DIVIDEND-RELIANCE INDUSTRIES LTD",
        "ACH CREDIT-DIVIDEND-TATA MOTORS SHAREHOLDERS",
        "INTEREST CR-SAVINGS ACCOUNT ANNUAL YIELD",
        "NEFT-CR-FREELANCE CLIENT TECH ADVISORY/PROJECT FEE",
        "UPI/UPWORK ESCROW INC/FREELANCE DESIGN INFLOW",
        "NEFT-CR-ZOMATO HYPERPURE PARTNER/WEEKLY RIDER INFLOW",
        "NEFT-CR-SWIGGY BUNDL TECHNOLOGIES/DELIVERY PAYOUT",
        "NEFT-CR-UBER INDIA DRIVER/WEEKLY TRIP EARNINGS"
    ],
    "Transfers": [
        "IMPS/P2P/TRANSFER TO SISTER NEETU/PERSONAL REPAY",
        "UPI/TRANSFER TO BROTHER AMIT SHARMA/GIFT AMOUNT",
        "IMPS/TRANSFER TO FATHER RAMESH CHANDER/MONTHLY HELP",
        "UPI/TRANSFER TO FRIEND PRIYA/WEEKEND SPLIT BILL",
        "UPI/TRANSFER TO VIKAS RAJ/DINNER SETTLEMENT SHARE",
        "IMPS/TRANSFER TO OWN ACCOUNT ICICI TO HDFC"
    ]
}

def generate_and_train_fallback():
    forbidden = get_forbidden_descriptions()
    print(f"Loaded {len(forbidden)} forbidden descriptions from demo_data/")

    corpus = []
    labels = []

    # Multiply variations with noise/suffixes to create a robust corpus
    variations = [
        "", " BANGALORE", " MUMBAI", " NEW DELHI", " PUNE", " HYDERABAD",
        " CHENNAI", " KOLKATA", " BRANCH", " RET", " ONLINE", " STORE"
    ]

    for cat, examples in RAW_SYNTHETIC_TEMPLATES.items():
        for ex in examples:
            clean_ex = ex.strip().upper()
            if clean_ex not in forbidden and clean_ex not in corpus:
                corpus.append(clean_ex)
                labels.append(cat)

            for var in variations:
                mod_desc = f"{clean_ex}{var}"
                if mod_desc not in forbidden and mod_desc not in corpus:
                    corpus.append(mod_desc)
                    labels.append(cat)

    print(f"Total synthetic training examples generated: {len(corpus)}")
    # Verify strict disjointness guarantee
    overlap = set(corpus).intersection(forbidden)
    assert len(overlap) == 0, f"Disjointness assertion failed! Found {len(overlap)} overlapping strings: {overlap}"
    print("Zero-overlap disjointness guarantee strictly verified: 0 overlapping strings with demo_data/.")

    # Save training corpus JSON and compute SHA-256
    corpus_dict = [{"description": d, "category": c} for d, c in zip(corpus, labels)]
    corpus_json_path = os.path.join(MODELS_DATA_DIR, "synthetic_training_corpus.json")
    corpus_bytes = json.dumps(corpus_dict, indent=2, sort_keys=True).encode("utf-8")
    with open(corpus_json_path, "wb") as f:
        f.write(corpus_bytes)

    corpus_hash = hashlib.sha256(corpus_bytes).hexdigest()
    print(f"Synthetic corpus saved to: {corpus_json_path}")
    print(f"Corpus SHA-256 Hash: {corpus_hash}")

    # Build and train scikit-learn pipeline: char n-grams + Logistic Regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2,
            sublinear_tf=True
        )),
        ("clf", LogisticRegression(
            C=3.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    pipeline.fit(corpus, labels)
    train_acc = pipeline.score(corpus, labels)
    print(f"Training accuracy on synthetic corpus: {round(train_acc * 100, 2)}%")

    # Save model artifact bundle
    model_bundle = {
        "pipeline": pipeline,
        "version": "1.0.0",
        "corpus_hash": corpus_hash,
        "classes": list(pipeline.classes_),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": len(corpus)
    }

    model_path = os.path.join(MODELS_DATA_DIR, "fallback_classifier_v1.joblib")
    joblib.dump(model_bundle, model_path)
    print(f"Fallback classifier model successfully persisted to: {model_path}")

    return corpus_hash, model_path

if __name__ == "__main__":
    generate_and_train_fallback()
