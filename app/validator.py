"""
Card number validation utilities.

Pure format/checksum validation and brand identification for payment card
numbers, based on publicly published standards:

  - Luhn algorithm (ISO/IEC 7812) for checksum validation.
  - IIN/BIN prefix ranges (also public, e.g. ISO/IEC 7812-1) for brand
    identification and expected length.

This module never contacts any card network, bank, or payment processor,
never stores input, and never generates full card numbers — only:
  (a) validates a number's format/checksum, and
  (b) computes the correct Luhn check digit for a *given* digit prefix,
      the same reference calculation used by every payment-form QA tool.

No real card data is used or required anywhere in this codebase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BrandRule:
    name: str
    pattern: re.Pattern
    lengths: tuple[int, ...]


# Publicly documented IIN/BIN prefix ranges for major card schemes.
# Sources: ISO/IEC 7812-1 prefix tables (widely republished, e.g. by the
# schemes' own public BIN documentation and standard open-source libraries
# such as jQuery.payment / Stripe.js card-type detection).
_BRAND_RULES: tuple[BrandRule, ...] = (
    BrandRule("Visa", re.compile(r"^4\d*$"), (13, 16, 19)),
    BrandRule(
        "Mastercard",
        re.compile(r"^(5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)\d*$"),
        (16,),
    ),
    BrandRule("American Express", re.compile(r"^3[47]\d*$"), (15,)),
    BrandRule(
        "Diners Club",
        re.compile(r"^(30[0-5]|36|38|39)\d*$"),
        (14,),
    ),
    BrandRule(
        "Discover",
        re.compile(r"^(6011|65|64[4-9]|622(1(2[6-9]|[3-9]\d)|[2-8]\d{2}|9([01]\d|2[0-5])))\d*$"),
        (16, 19),
    ),
    BrandRule("JCB", re.compile(r"^35(2[89]|[3-8]\d)\d*$"), (16,)),
    BrandRule("UnionPay", re.compile(r"^62\d*$"), (16, 17, 18, 19)),
    BrandRule("Maestro", re.compile(r"^(50|5[6-8]|63|67)\d*$"), (12, 13, 14, 15, 16, 17, 18, 19)),
)


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


def luhn_is_valid(number: str) -> bool:
    """Standard Luhn (mod 10) checksum check over a digit string."""
    digits = [int(d) for d in number]
    checksum = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def luhn_check_digit(partial_number: str) -> str:
    """Compute the check digit that makes `partial_number + digit` Luhn-valid."""
    digits = [int(d) for d in partial_number]
    checksum = 0
    # The check digit itself will sit at an "even" position (0-indexed from
    # the right, position 0), i.e. it is NOT doubled. Digits of the prefix
    # are doubled starting from the rightmost one.
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return str((10 - (checksum % 10)) % 10)


def detect_brand(digits: str) -> BrandRule | None:
    for rule in _BRAND_RULES:
        if rule.pattern.match(digits):
            return rule
    return None


def format_grouped(digits: str) -> str:
    return " ".join(digits[i : i + 4] for i in range(0, len(digits), 4))


def mask(digits: str) -> str:
    if len(digits) <= 4:
        return digits
    groups = []
    remaining = len(digits) - 4
    i = 0
    while i < remaining:
        chunk = min(4, remaining - i)
        groups.append("•" * chunk)
        i += chunk
    groups.append(digits[-4:])
    return " ".join(groups)


def validate(raw_number: str) -> dict:
    digits = _digits_only(raw_number)

    if not digits:
        return {
            "input": raw_number,
            "error": "no digits found in input",
        }

    if not (8 <= len(digits) <= 19):
        return {
            "input": raw_number,
            "number": digits,
            "valid_luhn": False,
            "valid_length": False,
            "brand": None,
            "length": len(digits),
            "error": "length out of plausible card-number range (8-19 digits)",
        }

    brand_rule = detect_brand(digits)
    valid_luhn = luhn_is_valid(digits)
    valid_length = len(digits) in brand_rule.lengths if brand_rule else (12 <= len(digits) <= 19)

    return {
        "input": raw_number,
        "number": digits,
        "brand": brand_rule.name if brand_rule else "Unknown",
        "length": len(digits),
        "valid_length": valid_length,
        "valid_luhn": valid_luhn,
        "valid": bool(valid_luhn and valid_length),
        "formatted": format_grouped(digits),
        "masked": mask(digits),
    }

