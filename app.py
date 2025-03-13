import os
import re
import cv2
import numpy as np
from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Regex pattern for Service Tag (Improved)
pattern = r'(?:st|svc\s*tag|service\s*tag|s\/n)[:\s]*([a-zA-Z0-9]{7})'

# Ensure upload folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocess image for better OCR accuracy"""
    try:
        logger.info(f"Loading image from {image_path}")
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            logger.error(f"Failed to load image at {image_path}")
            return None
        
        logger.info("Applying adaptive threshold")
        processed = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        processed_path = os.path.join(UPLOAD_FOLDER, "processed.jpg")
        cv2.imwrite(processed_path, processed)
        logger.info(f"Processed image saved to {processed_path}")
        
        return processed_path
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Service Tag Detection API is running"}), 200

@app.route("/upload", methods=["POST"])
def upload_file():
    logger.info(f"Upload endpoint accessed. Content-Type: {request.content_type}")
    
    if "image" not in request.files:
        logger.warning("No image key in request.files")
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files["image"]
    logger.info(f"File received: {file.filename}")
    
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
        file.save(filepath)
        logger.info(f"File saved to {filepath}")
        
        # Preprocess image
        processed_path = preprocess_image(filepath)
        if not processed_path:
            return jsonify({"error": "Failed to process image"}), 500
        
        # Perform OCR
        results = ocr.ocr(processed_path, cls=True)
        detected_texts = []
        service_tag = None

        if results and isinstance(results, list) and all(isinstance(r, list) for r in results):
            for result in results:
                for word_info in result:
                    if isinstance(word_info, list) and len(word_info) > 1:
                        text = word_info[1][0]
                        confidence = word_info[1][1]
                        detected_texts.append(text)
                        logger.info(f"Detected text: '{text}' with confidence {confidence}")
                        
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            service_tag = match.group(1)
                            logger.info(f"Service tag found: {service_tag}")
                            
                            # Delete temp file before returning
                            os.remove(processed_path)
                            return jsonify({"service_tag": service_tag, "confidence": round(confidence, 2)})
        
        logger.info(f"No service tag found. Detected texts: {detected_texts}")
        os.remove(processed_path)
        return jsonify({"error": "No Service Tag detected", "detected_texts": detected_texts}), 404

    except Exception as e:
        logger.error(f"Exception in upload_file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    from waitress import serve
    logger.info("Starting Service Tag OCR API server with Waitress...")
    serve(app, host="0.0.0.0", port=5000)
