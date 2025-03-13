import re
from paddleocr import PaddleOCR

# Initialize OCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")

# Image path
image_path = r"C:\Users\sowbh\Downloads\Service tag extraction\WhatsApp Image 2025-01-29 at 1.10.36 PM (1).jpeg"

# Perform OCR
results = ocr.ocr(image_path, cls=True)

# Define regex pattern to match different service tag formats
pattern = r'(?:ST|SVC TAG|SERVICE TAG|S\/N)[:\s]*([A-Z0-9]{7})'

# Extract service tag
service_tag = None
for line in results:
    for word_info in line:
        text = word_info[1][0]
        confidence = word_info[1][1]

        # Search for service tag using regex
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            service_tag = match.group(1)
            print(f"✅ Detected Service Tag: {service_tag} (Confidence: {confidence:.2f})")

if not service_tag:
    print("❌ No Service Tag detected.")
