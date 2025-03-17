#!/bin/bash

# Update system and install dependencies
apt-get update && apt-get install -y mupdf mupdf-tools

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt
