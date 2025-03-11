from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
from paddleocr import PaddleOCR
import re
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ocr = PaddleOCR(use_angle_cls=True, lang='en')

def process_ocr_result(result):
    """Extract service tag from OCR results."""
    try:
        if result and len(result) > 0:
            pattern = r'(?:ST|SVC TAG|SERVICE TAG|S\/N)[:\s]*([a-zA-Z0-9]{7})'
            text = ' '.join([line[1][0] for line in result[0] if len(line) >= 2])

            match = re.search(pattern, text)
            if match:
                return match.group(1)

            lines = [line[1][0].strip().upper() for line in result[0] if len(line) >= 2]
            for i in range(len(lines) - 1):
                if re.search(r'SERVICE\s*TAG\s*:?$', lines[i], re.IGNORECASE):
                    if re.match(r'^[A-Z0-9]{7}$', lines[i + 1]):
                        return lines[i + 1]

            for line in lines:
                match = re.search(r'\b([A-Z0-9]{7})\b', line)
                if match:
                    return match.group(1)

    except Exception as e:
        logger.error(f"Error processing OCR result: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    if 'frame' not in request.files:
        return jsonify({"status": "error", "message": "No frame uploaded"})

    try:
        frame = request.files['frame'].read()
        nparr = np.frombuffer(frame, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        result_original = ocr.ocr(image, cls=True)
        result_processed = ocr.ocr(thresh, cls=True)

        found_tag = process_ocr_result(result_original) or process_ocr_result(result_processed)

        if found_tag:
            return jsonify({"status": "success", "tag": found_tag})
        return jsonify({"status": "error", "message": "No service tag detected"})

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return jsonify({"status": "error", "message": f"Processing error: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
