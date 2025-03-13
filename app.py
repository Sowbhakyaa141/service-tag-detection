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
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang="en")

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Regex pattern to match Service Tag format
pattern = r'(?:ST|SVC TAG|SERVICE TAG|S\/N)[:\s]*([A-Z0-9]{7})'

# Ensure upload folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
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
        # Apply adaptive thresholding to enhance contrast
        processed = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Save processed image
        processed_path = os.path.join(UPLOAD_FOLDER, "processed.jpg")
        cv2.imwrite(processed_path, processed)
        logger.info(f"Processed image saved to {processed_path}")
        
        return processed_path
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    """Home route to verify API is running"""
    logger.info("Home endpoint accessed")
    return jsonify({"message": "Service Tag Detection API is running"}), 200

@app.route("/test", methods=["POST"])
def test_upload():
    """Simple test endpoint to verify file upload functionality"""
    logger.info(f"Test upload endpoint accessed with content type: {request.content_type}")
    logger.info(f"Files in request: {list(request.files.keys())}")
    
    if "image" not in request.files:
        logger.warning("No image key in request.files")
        return jsonify({"error": "No image uploaded", "files_found": list(request.files.keys())}), 400
    
    file = request.files["image"]
    logger.info(f"File received: {file.filename}")
    
    return jsonify({
        "success": True,
        "filename": file.filename,
        "content_type": file.content_type
    }), 200

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle image upload and perform OCR"""
    logger.info(f"Upload endpoint accessed with content type: {request.content_type}")
    logger.info(f"Files in request: {list(request.files.keys())}")
    
    # Check if any file is in the request
    if "image" not in request.files:
        logger.warning("No image key in request.files")
        return jsonify({
            "error": "No image uploaded", 
            "files_found": list(request.files.keys()),
            "content_type": request.content_type
        }), 400
    
    file = request.files["image"]
    logger.info(f"File received: {file.filename}")
    
    # Validate file
    if file.filename == "":
        logger.warning("Empty filename received")
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file extension: {file.filename}")
        return jsonify({"error": f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}"}), 400
    
    try:
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"File saved to {filepath}")
        
        # Check if file exists after saving
        if not os.path.exists(filepath):
            logger.error(f"Failed to save file at {filepath}")
            return jsonify({"error": "File save failed"}), 500
        
        # Preprocess image
        processed_path = preprocess_image(filepath)
        if processed_path is None or not os.path.exists(processed_path):
            logger.error("Image preprocessing failed")
            return jsonify({"error": "Failed to process image"}), 500
        
        logger.info("Running OCR on processed image")
        # Perform OCR
        results = ocr.ocr(processed_path, cls=True)
        
        # Extract Service Tag
        service_tag = None
        detected_texts = []  # Store detected text for debugging
        
        if results and isinstance(results, list):
            logger.info(f"OCR returned {len(results)} results")
            
            for result in results:
                if isinstance(result, list):
                    for word_info in result:
                        if isinstance(word_info, list) and len(word_info) > 1:
                            text = word_info[1][0]  # Extract text
                            confidence = word_info[1][1]  # Extract confidence score
                            detected_texts.append(text)
                            logger.info(f"Detected text: '{text}' with confidence {confidence}")
                            
                            # Check for Service Tag
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                service_tag = match.group(1)
                                logger.info(f"Service tag found: {service_tag}")
                                return jsonify({
                                    "service_tag": service_tag, 
                                    "confidence": round(confidence, 2)
                                })
        else:
            logger.warning("OCR returned no results or invalid format")
        
        logger.info(f"No service tag found. Detected {len(detected_texts)} text segments")
        return jsonify({
            "error": "No Service Tag detected", 
            "detected_texts": detected_texts
        }), 404
        
    except Exception as e:
        logger.error(f"Exception in upload_file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    logger.info("Starting Service Tag OCR API server...")
    app.run(host="0.0.0.0", port=5000, debug=True)