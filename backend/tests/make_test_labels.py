from PIL import Image, ImageDraw, ImageFont

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_reg = ImageFont.truetype(font_path, 26)
f_bold = ImageFont.truetype(font_bold, 26)

img = Image.new("RGB", (700, 500), "white")
d = ImageDraw.Draw(img)

lines = [
    ("NUTRI CRUNCH BISCUITS", f_bold),
    ("", f_reg),
    ("Net Qty: 200 g", f_reg),
    ("MRP Rs. 95.00 (Incl. of all taxes)", f_reg),
    ("Mfg. Date: 04/2026", f_reg),
    ("Mfd. by: XYZ Foods Pvt. Ltd., Plot 12,", f_reg),
    ("MIDC, Mumbai, Maharashtra 400001", f_reg),
    ("Consumer Care: 1800-123-4567,", f_reg),
    ("care@xyzfoods.example.com", f_reg),
    ("Country of Origin: India", f_reg),
]

y = 20
for text, font in lines:
    d.text((20, y), text, fill="black", font=font)
    y += 42

img.save("compliant_label.png")
print("saved compliant_label.png")

# --- A second, deliberately NON-compliant label (missing mfg date + no
#     "inclusive of all taxes" wording) to test that flags actually fire ---
img2 = Image.new("RGB", (700, 500), "white")
d2 = ImageDraw.Draw(img2)
lines2 = [
    ("SPICY MASALA CHIPS", f_bold),
    ("", f_reg),
    ("Net Qty: 50 g", f_reg),
    ("MRP Rs. 20.00", f_reg),
    ("Mfd. by: ABC Snacks Ltd, Delhi", f_reg),
]
y = 20
for text, font in lines2:
    d2.text((20, y), text, fill="black", font=font)
    y += 42
img2.save("noncompliant_label.png")
print("saved noncompliant_label.png")
