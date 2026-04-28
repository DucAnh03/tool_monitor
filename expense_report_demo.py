"""Task Description
================

Build a small command-line tool that analyzes expense data.

Requirements:
1. Accept expense rows from a CSV file with columns:
   `date,category,amount,note`
2. If no CSV path is provided, run against embedded demo data.
3. Validate each row:
   - `date` must use `YYYY-MM-DD`
   - `category` cannot be empty
   - `amount` must be a positive number
4. Ignore invalid rows, but report validation errors at the end.
5. Print a readable report with:
   - total spending
   - spending by category
   - spending by day
   - optional spending by month
   - the largest single expense

Usage:
    python expense_report_demo.py
    python expense_report_demo.py expenses.csv
    python expense_report_demo.py expenses.csv --top 3
    python expense_report_demo.py expenses.csv --monthly
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path


SAMPLE_CSV = """date,category,amount,note
2026-04-01,Food,12.50,Lunch
2026-04-01,Transport,8.75,Bus card top-up
2026-04-02,Utilities,45.00,Internet bill
2026-04-03,Food,18.20,Dinner
2026-04-03,Transport,78.20,Ride to airport
2026-04-04,Shopping,59.99,Keyboard
2026-04-05,Travel,abc,Taxi
"""


@dataclass(frozen=True)
class Expense:
    spent_on: date
    category: str
    amount: Decimal
    note: str


@dataclass(frozen=True)
class Report:
    total_spent: Decimal
    by_category: list[tuple[str, Decimal]]
    by_day: list[tuple[date, Decimal]]
    by_month: list[tuple[str, Decimal]]
    largest_expense: Expense | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze expenses from a CSV file or built-in demo data."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        help="Optional path to a CSV file with columns: date,category,amount,note",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of category/day rows to display in each section (default: 5).",
    )
    parser.add_argument(
        "--monthly",
        action="store_true",
        help="Include a spending-by-month section in the report.",
    )
    return parser.parse_args()


def parse_expense_row(
    row: dict[str, str | None], line_number: int
) -> tuple[Expense | None, str | None]:
    raw_date = clean_value(row.get("date"))
    raw_category = clean_value(row.get("category"))
    raw_amount = clean_value(row.get("amount"))
    raw_note = clean_value(row.get("note"))

    if not raw_date:
        return None, f"line {line_number}: missing date"
    if not raw_category:
        return None, f"line {line_number}: missing category"
    if not raw_amount:
        return None, f"line {line_number}: missing amount"

    try:
        spent_on = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return None, f"line {line_number}: invalid date '{raw_date}'"

    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        return None, f"line {line_number}: invalid amount '{raw_amount}'"

    if amount <= 0:
        return None, f"line {line_number}: amount must be positive"

    return Expense(
        spent_on=spent_on,
        category=raw_category,
        amount=amount,
        note=raw_note,
    ), None


def clean_value(value: str | None) -> str:
    return (value or "").strip()


def build_report(expenses: list[Expense]) -> Report:
    by_category_totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    by_day_totals: defaultdict[date, Decimal] = defaultdict(lambda: Decimal("0"))
    by_month_totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for expense in expenses:
        by_category_totals[expense.category] += expense.amount
        by_day_totals[expense.spent_on] += expense.amount
        by_month_totals[expense.spent_on.strftime("%Y-%m")] += expense.amount

    total_spent = sum((expense.amount for expense in expenses), start=Decimal("0"))
    by_category = sorted(
        by_category_totals.items(),
        key=lambda item: (-item[1], item[0].lower()),
    )
    by_day = sorted(by_day_totals.items(), key=lambda item: (-item[1], item[0]))
    by_month = sorted(by_month_totals.items(), key=lambda item: item[0])
    largest_expense = max(expenses, key=lambda expense: expense.amount, default=None)

    return Report(
        total_spent=total_spent,
        by_category=by_category,
        by_day=by_day,
        by_month=by_month,
        largest_expense=largest_expense,
    )


def format_money(amount: Decimal) -> str:
    return f"${amount:,.2f}"


def render_report(
    report: Report,
    valid_count: int,
    errors: list[str],
    source_label: str,
    top_n: int,
    include_monthly: bool,
) -> str:
    lines = [
        "Expense Report",
        "=" * 40,
        f"Source: {source_label}",
        f"Valid rows: {valid_count}",
        f"Invalid rows: {len(errors)}",
        f"Total spent: {format_money(report.total_spent)}",
    ]

    if report.largest_expense is None:
        lines.append("Largest expense: none")
    else:
        item = report.largest_expense
        lines.append(
            "Largest expense: "
            f"{format_money(item.amount)} | {item.category} | {item.spent_on.isoformat()} | {item.note or '-'}"
        )

    lines.append("")
    lines.append("Top Categories")
    lines.append("-" * 40)
    if report.by_category:
        for category, total in report.by_category[:top_n]:
            lines.append(f"{category:<15} {format_money(total)}")
    else:
        lines.append("No category data available.")

    lines.append("")
    lines.append("Top Spending Days")
    lines.append("-" * 40)
    if report.by_day:
        for spent_on, total in report.by_day[:top_n]:
            lines.append(f"{spent_on.isoformat():<15} {format_money(total)}")
    else:
        lines.append("No daily totals available.")

    if include_monthly:
        lines.append("")
        lines.append("Monthly Totals")
        lines.append("-" * 40)
        if report.by_month:
            for month, total in report.by_month:
                lines.append(f"{month:<15} {format_money(total)}")
        else:
            lines.append("No monthly totals available.")

    if errors:
        lines.append("")
        lines.append("Validation Errors")
        lines.append("-" * 40)
        lines.extend(errors)

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    try:
        if args.csv_path:
            path = Path(args.csv_path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                expenses, errors = parse_reader(reader)
            source_label = str(path.resolve())
        else:
            reader = csv.DictReader(StringIO(SAMPLE_CSV))
            expenses, errors = parse_reader(reader)
            source_label = "embedded demo data"
    except FileNotFoundError:
        print(f"Could not find CSV file: {args.csv_path}")
        return 1

    report = build_report(expenses)
    output = render_report(
        report=report,
        valid_count=len(expenses),
        errors=errors,
        source_label=source_label,
        top_n=max(args.top, 1),
        include_monthly=args.monthly,
    )
    print(output)
    return 0


def parse_reader(reader: csv.DictReader) -> tuple[list[Expense], list[str]]:
    expenses: list[Expense] = []
    errors: list[str] = []

    for line_number, row in enumerate(reader, start=2):
        expense, error = parse_expense_row(row, line_number)
        if error:
            errors.append(error)
            continue
        expenses.append(expense)

    return expenses, errors


if __name__ == "__main__":
    raise SystemExit(main())
