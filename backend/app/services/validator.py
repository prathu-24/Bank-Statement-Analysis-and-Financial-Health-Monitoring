from typing import List, Dict, Any, Tuple
from datetime import datetime
from app.schemas.transaction import NormalizedTransaction
from app.schemas.validation import ValidationReport, ValidationIssue

class StatementValidator:
    """
    Comprehensive validation engine for parsed bank statement transactions.
    Checks date integrity, balance consistency, duplicates, and missing values.
    """

    TOLERANCE: float = 1.00  # Currency rounding tolerance in INR

    @classmethod
    def validate(cls, transactions: List[NormalizedTransaction]) -> ValidationReport:
        if not transactions:
            return ValidationReport(
                is_valid=False,
                total_rows=0,
                valid_rows=0,
                error_count=1,
                warning_count=0,
                duplicate_count=0,
                balance_mismatch_count=0,
                issues=[
                    ValidationIssue(
                        level="ERROR",
                        code="EMPTY_STATEMENT",
                        message="No transaction records could be parsed from the provided statement."
                    )
                ],
                summary="Validation failed: 0 transactions parsed."
            )

        total_rows = len(transactions)
        issues: List[ValidationIssue] = []
        duplicate_count = 0
        balance_mismatch_count = 0
        error_rows = set()
        warning_rows = set()

        # 1. Duplicate Detection
        seen_keys: Dict[Tuple[str, str, float, float, float], int] = {}
        for idx, tx in enumerate(transactions, start=1):
            key = (
                tx.date,
                tx.description.strip().lower()[:50],
                round(tx.debit, 2),
                round(tx.credit, 2),
                round(tx.balance, 2)
            )
            if key in seen_keys:
                duplicate_count += 1
                first_row = seen_keys[key]
                warning_rows.add(idx)
                issues.append(
                    ValidationIssue(
                        level="WARNING",
                        code="DUPLICATE_TXN",
                        row_number=idx,
                        message=f"Duplicate transaction detected. Identical to row {first_row} (Date: {tx.date}, Amount: ₹{tx.debit or tx.credit:,.2f}).",
                        details={"original_row": first_row, "current_row": idx}
                    )
                )
            else:
                seen_keys[key] = idx

        # 2. Date and Field Integrity
        dates: List[str] = []
        for idx, tx in enumerate(transactions, start=1):
            # Check date format
            try:
                datetime.strptime(tx.date, "%Y-%m-%d")
                dates.append(tx.date)
            except (ValueError, TypeError):
                error_rows.add(idx)
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        code="INVALID_DATE",
                        row_number=idx,
                        message=f"Row {idx} has an invalid or unrecognized date format: '{tx.date}'.",
                    )
                )

            # Check for negative amounts
            if tx.debit < 0 or tx.credit < 0:
                error_rows.add(idx)
                issues.append(
                    ValidationIssue(
                        level="ERROR",
                        code="NEGATIVE_AMOUNT",
                        row_number=idx,
                        message=f"Row {idx} contains negative amount: Debit=₹{tx.debit}, Credit=₹{tx.credit}."
                    )
                )

            # Check missing description
            if not tx.description or tx.description.strip() in ("", "Unknown", "NaN"):
                warning_rows.add(idx)
                issues.append(
                    ValidationIssue(
                        level="WARNING",
                        code="MISSING_DESCRIPTION",
                        row_number=idx,
                        message=f"Row {idx} has an empty or missing description."
                    )
                )

        # 3. Balance Arithmetic Verification
        # Determine whether statement order is ascending (oldest first) or descending (newest first)
        is_ascending = True
        if len(transactions) >= 2:
            try:
                d1 = datetime.strptime(transactions[0].date, "%Y-%m-%d")
                d_last = datetime.strptime(transactions[-1].date, "%Y-%m-%d")
                if d1 > d_last:
                    is_ascending = False
            except Exception:
                is_ascending = True

        for i in range(len(transactions) - 1):
            if is_ascending:
                prev_tx = transactions[i]
                curr_tx = transactions[i + 1]
                expected_balance = prev_tx.balance + curr_tx.credit - curr_tx.debit
                diff = abs(curr_tx.balance - expected_balance)
                checked_row = i + 2  # 1-indexed row for curr_tx
            else:
                curr_tx = transactions[i]
                prev_tx = transactions[i + 1]
                expected_balance = prev_tx.balance + curr_tx.credit - curr_tx.debit
                diff = abs(curr_tx.balance - expected_balance)
                checked_row = i + 1

            if diff > cls.TOLERANCE:
                balance_mismatch_count += 1
                warning_rows.add(checked_row)
                issues.append(
                    ValidationIssue(
                        level="WARNING",
                        code="BALANCE_MISMATCH",
                        row_number=checked_row,
                        message=(
                            f"Balance inconsistency at row {checked_row}: "
                            f"Reported balance ₹{curr_tx.balance:,.2f} differs from expected "
                            f"₹{expected_balance:,.2f} by ₹{diff:,.2f} "
                            f"(Prev: ₹{prev_tx.balance:,.2f}, +Credit: ₹{curr_tx.credit:,.2f}, -Debit: ₹{curr_tx.debit:,.2f})."
                        ),
                        details={
                            "row": checked_row,
                            "reported_balance": curr_tx.balance,
                            "expected_balance": round(expected_balance, 2),
                            "difference": round(diff, 2)
                        }
                    )
                )

        error_count = len([iss for iss in issues if iss.level == "ERROR"])
        warning_count = len([iss for iss in issues if iss.level == "WARNING"])
        valid_rows = total_rows - len(error_rows)

        date_start = min(dates) if dates else None
        date_end = max(dates) if dates else None

        is_valid = error_count == 0

        summary = (
            f"Successfully verified {valid_rows}/{total_rows} rows. "
            f"Found {warning_count} warnings ({duplicate_count} duplicates, {balance_mismatch_count} balance drifts) "
            f"and {error_count} fatal errors."
        )

        return ValidationReport(
            is_valid=is_valid,
            total_rows=total_rows,
            valid_rows=valid_rows,
            error_count=error_count,
            warning_count=warning_count,
            duplicate_count=duplicate_count,
            balance_mismatch_count=balance_mismatch_count,
            date_range_start=date_start,
            date_range_end=date_end,
            issues=issues,
            summary=summary
        )

