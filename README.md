# LabelCheck AI — Prototype

**SIH26034** — Software System to Check Compliance of Packaged Commodities
under Legal Metrology (Packaged Commodities) Rules, 2011, by Scanning
Products, Images and Labels.

Photograph a product label → OCR reads it → a rule engine checks it against
every mandatory declaration in **Rule 6 of the LMPC Rules, 2011** → get a
per-field Compliant / Non-Compliant / Not Detected report.

## This has been tested, not just written

Unlike a mockup, the actual OCR → rule-engine pipeline in this prototype has
been run end-to-end against two synthetic test labels (see `backend/tests/`):
one fully compliant, one deliberately missing/incorrect on two fields. The
pipeline correctly identified every planted issue. You can re-run this
yourself:

```
cd backend/tests
python3 test_pipeline.py
```

This proves the **hard part** (OCR text extraction + regex-based field
validation) genuinely works — not just that the code compiles.

## Run it

```
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

Also install the Tesseract OCR engine (a separate binary, not just a pip
package) if you don't have it:
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: https://github.com/UB-Mannheim/tesseract/wiki

Then open **http://localhost:8000** — one server handles both the site and
the API, no separate frontend process needed.

## What it checks (Rule 6, LMPC Rules 2011)

| Field | What's validated |
|---|---|
| Manufacturer / Packer / Importer | Name & address present |
| Net Quantity | Present, with a standard unit (g/kg/ml/l) |
| Month & Year of Manufacture | Present |
| MRP | Present **and** explicitly says "inclusive of all taxes" (Rule 18) |
| Consumer Care Contact | Phone number or email present |
| Country of Origin | Present (only mandatory for imported goods — informational otherwise) |

## Project structure

```
labelcheck-ai/
├── backend/
│   ├── main.py          FastAPI app — OCR pipeline + API + serves frontend
│   ├── rules.py          Rule 6 field extraction & validation logic
│   ├── requirements.txt
│   └── tests/
│       ├── test_pipeline.py       End-to-end pipeline test (see above)
│       ├── make_test_labels.py    Regenerates the two test label images
│       ├── compliant_label.png
│       └── noncompliant_label.png
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Honest limitations (say this out loud in your demo — judges respect it)

- **This is regex/keyword-based, not a trained NLP model.** It's fast and
  explainable, but it can miss unusual phrasing or layouts it hasn't seen.
  The fix over time is expanding the keyword/pattern lists in `rules.py`,
  not retraining a model.
- **OCR accuracy depends heavily on photo quality.** The test labels above
  are clean, computer-rendered text — real crumpled/glossy product labels
  will be harder. Encourage close, well-lit, flat shots.
- **"Common/generic name of commodity"** (one of the seven Rule 6 fields)
  isn't checked here — it's difficult to validate reliably without a
  product-category reference database, and was intentionally left out
  rather than faked with a low-confidence guess.
- **Country of Origin is treated as informational**, not blocking, since
  it's only mandatory for imported goods and this prototype has no way to
  know if a given product is imported.
- **No multilingual OCR yet** — regional-language declarations (Hindi,
  etc.) won't be picked up by the current regex patterns, which are
  English-only.

## Natural next steps

- Add barcode/QR lookup (Open Food Facts style) as a fallback when OCR
  confidence is low.
- Expand `rules.py` patterns from real scanned labels, not just synthetic
  test cases.
- Add an inspector-facing history log (SQLite/MySQL) of past scans, as
  described in the pitch deck's Technical Approach slide.
