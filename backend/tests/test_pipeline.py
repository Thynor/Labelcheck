import io
import json
import pytesseract
from PIL import Image, ImageOps
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."));
from rules import run_all_checks, compute_verdict


def preprocess_image(path):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    return img


def run_pipeline(path):
    img = preprocess_image(path)
    raw_text = pytesseract.image_to_string(img)
    print(f"\n{'='*60}\nOCR OUTPUT for {path}:\n{'-'*60}")
    print(raw_text)
    print("-" * 60)

    results = run_all_checks(raw_text)
    verdict = compute_verdict(results)

    print(f"VERDICT: {verdict['verdict'].upper()} — {verdict['summary']}\n")
    for r in results:
        print(f"  [{r.status.upper():13}] {r.label:32} -> {r.detected_value!r}")
        print(f"                 note: {r.note}")
    return verdict, results


print("\n\n########## TEST 1: COMPLIANT LABEL ##########")
v1, r1 = run_pipeline("compliant_label.png")

print("\n\n########## TEST 2: NON-COMPLIANT LABEL ##########")
v2, r2 = run_pipeline("noncompliant_label.png")

# ---- Assertions: sanity-check the pipeline actually works as intended ----
assert v1["verdict"] == "compliant", f"Expected compliant label to pass, got {v1}"
assert v2["verdict"] == "non_compliant", f"Expected non-compliant label to fail, got {v2}"

# Compliant label: every mandatory field should be found
for r in r1:
    if r.key != "country_of_origin":
        assert r.status == "compliant", f"Field {r.key} unexpectedly {r.status} on compliant label"

# Non-compliant label: MRP should be missing "inclusive of all taxes",
# and mfg_date should be not_detected (it was omitted on purpose)
mrp_result = next(r for r in r2 if r.key == "mrp")
assert mrp_result.status == "non_compliant", f"Expected MRP to be flagged, got {mrp_result.status}"

mfg_result = next(r for r in r2 if r.key == "mfg_date")
assert mfg_result.status == "not_detected", f"Expected mfg_date missing, got {mfg_result.status}"

print("\n\n✅ ALL ASSERTIONS PASSED — pipeline behaves correctly on both test cases.")
