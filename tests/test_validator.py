import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.validator import luhn_check_digit, luhn_is_valid, validate

# Well-known publicly documented test numbers (the same ones used in Stripe's
# and other processors' own public test-mode documentation) — not real cards.
VALID_CASES = {
    "4111111111111111": "Visa",
    "4012888888881881": "Visa",
    "5555555555554444": "Mastercard",
    "5105105105105100": "Mastercard",
    "2223003122003222": "Mastercard",
    "378282246310005": "American Express",
    "371449635398431": "American Express",
    "6011111111111117": "Discover",
    "3530111333300000": "JCB",
    "30569309025904": "Diners Club",
    "6200000000000005": "UnionPay",
}


def test_valid_numbers_detected_correctly():
    for number, expected_brand in VALID_CASES.items():
        result = validate(number)
        assert result["valid_luhn"] is True, number
        assert result["brand"] == expected_brand, (number, result)
        assert result["valid"] is True, result


def test_formatting_and_spaces_dashes_stripped():
    result = validate("4111-1111-1111-1111")
    assert result["number"] == "4111111111111111"
    assert result["formatted"] == "4111 1111 1111 1111"
    assert result["masked"] == "•••• •••• •••• 1111"


def test_invalid_luhn():
    result = validate("4111111111111112")
    assert result["valid_luhn"] is False
    assert result["valid"] is False


def test_unknown_brand_still_checks_luhn():
    result = validate("9999999999999999")
    assert result["brand"] == "Unknown"
    assert result["valid_luhn"] is False


def test_too_short_input_returns_error():
    result = validate("123")
    assert "error" in result


def test_empty_input_returns_error():
    result = validate("abc")
    assert "error" in result


def test_luhn_check_digit_matches_known_numbers():
    for number in VALID_CASES:
        prefix, expected_digit = number[:-1], number[-1]
        assert luhn_check_digit(prefix) == expected_digit
        assert luhn_is_valid(prefix + luhn_check_digit(prefix))

