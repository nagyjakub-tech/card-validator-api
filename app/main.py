"""
Card Validator API — Luhn checksum validation and card-brand/BIN
identification for payment card numbers, worldwide (any IIN/BIN scheme
covered by the public ISO/IEC 7812 prefix tables: Visa, Mastercard, Amex,
Discover, JCB, Diners Club, UnionPay, Maestro).

This is a pure format/checksum utility — the kind every checkout form uses
client-side to give instant "looks like a valid card number" feedback, or
that QA/test tooling uses to build Luhn-valid sandbox numbers. It never
contacts a card network, bank, or payment processor; never stores input;
and never returns or generates a real, complete card number.

Auth model: same as our other APIs — RapidAPI's proxy forwards every
request with an `X-RapidAPI-Proxy-Secret` header. We validate that header
so nobody can call this service directly and skip RapidAPI's billing.
Set the expected value via the RAPIDAPI_PROXY_SECRET environment variable.
If unset (local dev), auth is skipped.
"""
from __future__ import annotations

import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.validator import luhn_check_digit, validate

PROXY_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET")

app = FastAPI(
    title="Card Validator API",
    description=(
        "Validate payment card numbers (Luhn checksum + brand/BIN detection) "
        "for any country — Visa, Mastercard, Amex, Discover, JCB, Diners "
        "Club, UnionPay, Maestro. Pure format validation, no card network "
        "calls, no data stored."
    ),
    version="1.0.0",
)


class NumberRequest(BaseModel):
    number: str = Field(
        ...,
        min_length=6,
        max_length=32,
        description="Card number, digits only or with spaces/dashes.",
        examples=["4111 1111 1111 1111"],
    )


class CheckDigitRequest(BaseModel):
    partial_number: str = Field(
        ...,
        min_length=5,
        max_length=18,
        description="All digits of the card number except the last (check) digit.",
        examples=["411111111111111"],
    )


class ValidateResponse(BaseModel):
    input: str
    number: str | None = None
    brand: str | None = None
    length: int | None = None
    valid_length: bool | None = None
    valid_luhn: bool | None = None
    valid: bool | None = None
    formatted: str | None = None
    masked: str | None = None
    error: str | None = None


class CheckDigitResponse(BaseModel):
    partial_number: str
    check_digit: str
    full_number: str


@app.middleware("http")
async def verify_rapidapi_proxy(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json", "/"):
        return await call_next(request)
    if PROXY_SECRET:
        incoming = request.headers.get("x-rapidapi-proxy-secret")
        if incoming != PROXY_SECRET:
            return JSONResponse(
                status_code=403,
                content={"detail": "Missing/invalid RapidAPI proxy secret."},
            )
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time-Ms"] = str(round((time.time() - start) * 1000, 2))
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/validate", response_model=ValidateResponse)
def validate_number(req: NumberRequest):
    return validate(req.number)


@app.post("/v1/check-digit", response_model=CheckDigitResponse)
def check_digit(req: CheckDigitRequest):
    digits = "".join(c for c in req.partial_number if c.isdigit())
    if not digits:
        raise HTTPException(status_code=400, detail="partial_number must contain digits")
    digit = luhn_check_digit(digits)
    return CheckDigitResponse(
        partial_number=digits,
        check_digit=digit,
        full_number=digits + digit,
    )

