# Card Validator API

API na overenie platobných kariet — Luhn kontrolný súčet + rozpoznanie
značky karty (Visa, Mastercard, Amex, Discover, JCB, Diners Club, UnionPay,
Maestro) podľa verejne známych BIN/IIN rozsahov. Funguje pre celý svet, nie
len jednu krajinu. Žiadne volania na platené AI API ani na kartové siete —
je to čisto matematika a verejne publikované tabuľky, takže náklad na jedno
použitie je prakticky nulový.

**Dôležité:** toto API nekontaktuje žiadnu banku ani platobný systém,
neukladá žiadne vstupy a negeneruje kompletné čísla kariet. Robí presne to,
čo bežne robí každý nákupný formulár pri zadávaní karty — overí formát a
dá vizuálnu spätnú väzbu ("toto vyzerá ako platná Visa karta").

## Čo to robí

- **`POST /v1/validate`** — overí Luhn kontrolný súčet, rozpozná značku
  karty a dĺžku čísla, vráti formátovaný a maskovaný výstup.
- **`POST /v1/check-digit`** — pre zadaný prefix čísla (všetky číslice okrem
  poslednej) dopočíta správnu kontrolnú číslicu. Užitočné pre generovanie
  testovacích/sandbox čísel v QA nástrojoch (rovnaký princíp ako verejne
  známe testovacie čísla od Stripe a pod.).

### Príklad

```bash
curl -X POST http://127.0.0.1:8000/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"number": "4111 1111 1111 1111"}'
```

Odpoveď:
```json
{
  "input": "4111 1111 1111 1111",
  "number": "4111111111111111",
  "brand": "Visa",
  "length": 16,
  "valid_length": true,
  "valid_luhn": true,
  "valid": true,
  "formatted": "4111 1111 1111 1111",
  "masked": "•••• •••• •••• 1111"
}
```

## Lokálne spustenie

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -v
```

## Nasadenie na verejný server

Rovnaký postup ako pri predchádzajúcej appke — Render.com, free plán, Docker:

1. Nahraj repozitár na GitHub.
2. Na Rendri: "New" → "Web Service" → napoj repozitár → "Docker" build.
3. Over: `curl https://tvoja-url.onrender.com/health` → `{"status":"ok"}`.

## Napojenie na RapidAPI

Rovnaký postup ako pri SK/CZ Text Tools API — nová API v RapidAPI Studiu,
Base URL na Render adresu, `X-RapidAPI-Proxy-Secret` do premennej
`RAPIDAPI_PROXY_SECRET` v Renderi, endpointy `/v1/validate` a
`/v1/check-digit`, kategória napr. "Financial" alebo "Tools".

## Štruktúra projektu

```
app/
  main.py       - FastAPI server, endpointy, autentifikácia
  validator.py  - Luhn algoritmus, BIN/značka detekcia
tests/          - automatizované testy (pytest)
Dockerfile      - build a spustenie servera
```
