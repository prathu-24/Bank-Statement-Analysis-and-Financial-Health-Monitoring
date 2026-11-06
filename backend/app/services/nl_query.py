import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session

from app.models.transaction import TransactionModel
from app.services.sanitizer import DataSanitizer
from app.services.telemetry import NetworkTracker

class StatementQueryEngine:
    """
    Structured natural-language query processor.
    Translates questions into a validated, deterministic StructuredQuerySpec.
    Executes the spec locally via Pandas with full source-row audit trails.
    NEVER executes raw SQL from any model or prompt.
    """

    MONTH_MAP = {
        "january": "01", "jan": "01",
        "february": "02", "feb": "02",
        "march": "03", "mar": "03",
        "april": "04", "apr": "04",
        "may": "05",
        "june": "06", "jun": "06",
        "july": "07", "jul": "07",
        "august": "08", "aug": "08",
        "september": "09", "sep": "09", "sept": "09",
        "october": "10", "oct": "10",
        "november": "11", "nov": "11",
        "december": "12", "dec": "12"
    }

    CATEGORIES = [
        "Food & Dining", "Shopping", "Groceries", "Utilities & Bills",
        "Housing & Rent", "Transportation", "Entertainment", "Healthcare",
        "Investments", "Loans & EMI", "Charges", "Income"
    ]

    @classmethod
    def parse_offline_intent(cls, question: str, known_merchants: List[str]) -> Dict[str, Any]:
        """
        Deterministic, local rule-based intent extractor.
        Produces a strict StructuredQuerySpec without external network calls.
        """
        q = question.lower().strip()

        spec = {
            "intent": "search_transactions",
            "merchant": None,
            "category": None,
            "month": None,
            "metric": "sum",
            "sort_by": "date",
            "ascending": False,
            "limit": 10
        }

        # 1. Month detection
        for m_name, m_num in cls.MONTH_MAP.items():
            if re.search(r'\b' + m_name + r'\b', q):
                spec["month"] = m_num
                break
        # Also check YYYY-MM
        m_regex = re.search(r'\b(20\d{2})-(0[1-9]|1[0-2])\b', q)
        if m_regex:
            spec["month"] = m_regex.group(0)

        # 2. Category detection
        for cat in cls.CATEGORIES:
            key = cat.lower().split("&")[0].strip()
            if key in q or cat.lower() in q:
                spec["category"] = cat
                break

        # 3. Merchant detection
        for m in sorted(known_merchants, key=len, reverse=True):
            if m and len(m) >= 3 and m.lower() in q:
                spec["merchant"] = m
                break

        # If no known merchant found, check common brand patterns
        if not spec["merchant"]:
            for brand in ["swiggy", "zomato", "uber", "ola", "amazon", "flipkart", "netflix", "spotify", "cult.fit", "zepto", "blinkit", "airtel", "jio"]:
                if brand in q:
                    spec["merchant"] = brand.capitalize()
                    break

        # 4. Intent & Metric detection
        if any(w in q for w in ["biggest", "largest", "maximum", "highest expense", "biggest bill", "biggest recurring"]):
            spec["intent"] = "largest_expense"
            spec["metric"] = "max"
            spec["sort_by"] = "debit"
            spec["ascending"] = False
            spec["limit"] = 5
        elif any(w in q for w in ["highest balance", "maximum balance", "peak balance"]):
            spec["intent"] = "highest_balance"
            spec["metric"] = "max"
            spec["sort_by"] = "balance"
            spec["ascending"] = False
            spec["limit"] = 1
        elif any(w in q for w in ["lowest balance", "minimum balance", "lowest cash"]):
            spec["intent"] = "lowest_balance"
            spec["metric"] = "min"
            spec["sort_by"] = "balance"
            spec["ascending"] = True
            spec["limit"] = 1
        elif any(w in q for w in ["how much", "total spent", "total spend", "how much did i spend"]):
            if spec["merchant"]:
                spec["intent"] = "spend_by_merchant"
            elif spec["category"]:
                spec["intent"] = "spend_by_category"
            else:
                spec["intent"] = "total_expense"
            spec["metric"] = "sum"
        elif any(w in q for w in ["total earned", "total income", "salary"]):
            spec["intent"] = "total_income"
            spec["metric"] = "sum"
        elif any(w in q for w in ["how many", "count"]):
            spec["intent"] = "transaction_count"
            spec["metric"] = "count"

        return spec

    @classmethod
    def execute_query(cls, question: str, db: Session) -> Dict[str, Any]:
        """
        Executes a question against the database.
        Returns the parsed spec, computed answer text, and contributing source rows.
        """
        # Fetch transactions
        txs = db.query(TransactionModel).all()
        if not txs:
            return {
                "question": question,
                "answer": "No statement transactions are loaded in the database.",
                "computed_value": 0.0,
                "structured_spec": {},
                "source_rows": [],
                "source_count": 0,
                "engine_used": "offline_rule_parser",
                "methodology": "Structured Query Spec parsed and executed deterministically locally via Pandas.",
                "assumptions": {"offline_local_processing": True}
            }

        # Convert to DataFrame
        data = []
        for t in txs:
            data.append({
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "merchant": t.normalized_merchant or "",
                "debit": float(t.debit or 0.0),
                "credit": float(t.credit or 0.0),
                "balance": float(t.balance or 0.0),
                "category": t.category or "Uncategorized",
                "source_page": t.source_page or 1,
                "source_row": t.source_row
            })
        df = pd.DataFrame(data)

        known_merchants = [m for m in df["merchant"].unique() if m]

        # Extract structured query spec
        spec = cls.parse_offline_intent(question, known_merchants)
        engine_used = "offline_rule_parser"

        # Optional Gemini parsing if key configured
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                import httpx
                # Only send sanitized query text
                masked_q = DataSanitizer.mask_sensitive_data(question)
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"Extract structured query spec from: '{masked_q}'. "
                                    f"Respond ONLY in valid JSON matching: {{\"intent\": str, \"merchant\": str or null, \"category\": str or null, \"month\": str or null, \"metric\": str}}"
                        }]
                    }]
                }
                # Log call to NetworkTracker
                NetworkTracker.record_call("https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent")
                # Attempt call with timeout
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                resp = httpx.post(url, json=payload, timeout=3.0)
                if resp.status_code == 200:
                    import json
                    txt = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    clean_json = re.search(r'\{.*\}', txt, re.DOTALL)
                    if clean_json:
                        parsed_llm = json.loads(clean_json.group(0))
                        for k, v in parsed_llm.items():
                            if v is not None:
                                spec[k] = v
                        engine_used = "gemini_structured_parser"
            except Exception:
                # Fallback to local rule engine silently
                engine_used = "offline_rule_parser"

        # Execute the structured query spec on DataFrame
        filtered = df.copy()

        # Apply month filter
        if spec.get("month"):
            m_val = spec["month"]
            if len(m_val) == 2:  # MM
                filtered = filtered[filtered["date"].str.contains(f"-{m_val}-", na=False)]
            elif len(m_val) == 7:  # YYYY-MM
                filtered = filtered[filtered["date"].str.startswith(m_val)]

        # Apply merchant filter
        if spec.get("merchant"):
            m_target = spec["merchant"].lower()
            filtered = filtered[
                filtered["merchant"].str.lower().str.contains(m_target, na=False) |
                filtered["description"].str.lower().str.contains(m_target, na=False)
            ]

        # Apply category filter
        if spec.get("category"):
            filtered = filtered[filtered["category"].str.lower() == spec["category"].lower()]

        # Generate computed answer based on intent
        intent = spec.get("intent")
        computed_val = 0.0
        answer = ""

        if intent in ("spend_by_merchant", "spend_by_category", "total_expense"):
            debits_df = filtered[filtered["debit"] > 0]
            computed_val = float(debits_df["debit"].sum())
            rows = debits_df.sort_values(by="date", ascending=False).to_dict(orient="records")

            target_name = spec.get("merchant") or spec.get("category") or "total expenses"
            month_suffix = f" in {spec['month']}" if spec.get("month") else ""
            answer = f"You spent ₹{computed_val:,.2f} on {target_name}{month_suffix} across {len(rows)} verified transaction(s)."

        elif intent == "total_income":
            credits_df = filtered[filtered["credit"] > 0]
            computed_val = float(credits_df["credit"].sum())
            rows = credits_df.sort_values(by="date", ascending=False).to_dict(orient="records")
            month_suffix = f" in {spec['month']}" if spec.get("month") else ""
            answer = f"Total verified income received was ₹{computed_val:,.2f}{month_suffix} across {len(rows)} deposit(s)."

        elif intent == "largest_expense":
            debits_df = filtered[filtered["debit"] > 0].sort_values(by="debit", ascending=False)
            if not debits_df.empty:
                top_tx = debits_df.iloc[0]
                computed_val = float(top_tx["debit"])
                rows = debits_df.head(spec.get("limit", 5)).to_dict(orient="records")
                answer = f"Your largest expense was ₹{computed_val:,.2f} at '{top_tx['description']}' on {top_tx['date']} ({top_tx['category']})."
            else:
                rows = []
                answer = "No debit transactions matching that criteria were found."

        elif intent == "highest_balance":
            sorted_bal = df.sort_values(by="balance", ascending=False)
            if not sorted_bal.empty:
                peak = sorted_bal.iloc[0]
                computed_val = float(peak["balance"])
                rows = [peak.to_dict()]
                answer = f"Your peak statement closing balance was ₹{computed_val:,.2f} recorded on {peak['date']}."
            else:
                rows = []
                answer = "No balance history available."

        elif intent == "lowest_balance":
            sorted_bal = df.sort_values(by="balance", ascending=True)
            if not sorted_bal.empty:
                trough = sorted_bal.iloc[0]
                computed_val = float(trough["balance"])
                rows = [trough.to_dict()]
                answer = f"Your lowest statement closing balance was ₹{computed_val:,.2f} recorded on {trough['date']}."
            else:
                rows = []
                answer = "No balance history available."

        else:  # General search
            rows = filtered.head(spec.get("limit", 10)).to_dict(orient="records")
            computed_val = len(rows)
            answer = f"Found {len(rows)} matching transaction(s) for your inquiry."

        return {
            "question": question,
            "answer": answer,
            "computed_value": round(computed_val, 2),
            "structured_spec": spec,
            "source_rows": rows[:20],
            "source_count": len(rows),
            "engine_used": engine_used,
            "methodology": "Structured Query Spec parsed locally (or via optional sanitized LLM), evaluated through Pandas query execution with 100% source-row provenance.",
            "assumptions": {
                "safe_execution": "Strictly StructuredQuerySpec filters; zero raw SQL generation.",
                "pii_protection": "Only masked strings submitted to any external query model."
            }
        }

