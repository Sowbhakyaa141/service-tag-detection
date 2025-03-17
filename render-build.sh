#!/bin/bash
apt-get update && apt-get install -y mupdf mupdf-tools
pip install --upgrade pip
pip install -r requirements.txt

