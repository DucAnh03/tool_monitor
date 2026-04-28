"""Small command-line unit converter.

Usage:
    python unit_converter.py 10 km mi
    python unit_converter.py 72 f c
    python unit_converter.py 2.5 kg lb
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation


LINEAR_UNITS: dict[str, tuple[str, Decimal]] = {
    "mm": ("length", Decimal("0.001")),
    "cm": ("length", Decimal("0.01")),
    "m": ("length", Decimal("1")),
    "km": ("length", Decimal("1000")),
    "in": ("length", Decimal("0.0254")),
    "ft": ("length", Decimal("0.3048")),
    "yd": ("length", Decimal("0.9144")),
    "mi": ("length", Decimal("1609.344")),
    "g": ("weight", Decimal("1")),
    "kg": ("weight", Decimal("1000")),
    "oz": ("weight", Decimal("28.349523125")),
    "lb": ("weight", Decimal("453.59237")),
}

TEMPERATURE_UNITS = {"c", "f", "k"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert common units from the CLI.")
    parser.add_argument("value", help="Numeric value to convert.")
    parser.add_argument("from_unit", help="Source unit, for example km, mi, c, f.")
    parser.add_argument("to_unit", help="Target unit, for example m, ft, k, lb.")
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        help="Decimal places to show in the result (default: 4).",
    )
    return parser.parse_args()


def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric value: {value}") from exc


def convert_linear(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    from_kind, from_factor = LINEAR_UNITS[from_unit]
    to_kind, to_factor = LINEAR_UNITS[to_unit]
    if from_kind != to_kind:
        raise ValueError(f"cannot convert {from_kind} unit to {to_kind} unit")
    return value * from_factor / to_factor


def convert_temperature(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    if from_unit == "c":
        celsius = value
    elif from_unit == "f":
        celsius = (value - Decimal("32")) * Decimal("5") / Decimal("9")
    else:
        celsius = value - Decimal("273.15")

    if to_unit == "c":
        return celsius
    if to_unit == "f":
        return celsius * Decimal("9") / Decimal("5") + Decimal("32")
    return celsius + Decimal("273.15")


def convert(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    if from_unit in LINEAR_UNITS and to_unit in LINEAR_UNITS:
        return convert_linear(value, from_unit, to_unit)
    if from_unit in TEMPERATURE_UNITS and to_unit in TEMPERATURE_UNITS:
        return convert_temperature(value, from_unit, to_unit)

    supported = ", ".join(sorted(set(LINEAR_UNITS) | TEMPERATURE_UNITS))
    raise ValueError(f"unsupported unit pair. Supported units: {supported}")


def format_decimal(value: Decimal, precision: int) -> str:
    places = max(precision, 0)
    quantizer = Decimal("1").scaleb(-places)
    return f"{value.quantize(quantizer):f}"


def main() -> int:
    args = parse_args()

    try:
        value = parse_decimal(args.value)
        converted = convert(value, args.from_unit, args.to_unit)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print(
        f"{format_decimal(value, args.precision)} {args.from_unit.lower()} = "
        f"{format_decimal(converted, args.precision)} {args.to_unit.lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
