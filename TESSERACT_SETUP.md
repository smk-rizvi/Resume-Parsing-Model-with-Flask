# Tesseract OCR Setup Guide

To enable image resume processing, you need to install Tesseract OCR on your system.

## Windows Installation

1. **Download Tesseract:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (usually tesseract-ocr-w64-setup-v5.x.x.exe)

2. **Install Tesseract:**
   - Run the installer as Administrator
   - Install to the default location: `C:\Program Files\Tesseract-OCR\`
   - Make sure to check "Add to PATH" during installation

3. **Verify Installation:**
   - Open Command Prompt
   - Type: `tesseract --version`
   - You should see version information

4. **Restart the Application:**
   - Stop the Flask app (Ctrl+C)
   - Restart: `python app.py`
   - Now image processing should work

## Alternative: Use PDF/DOCX Instead

If you don't want to install Tesseract, simply:
1. Convert your resume image to PDF (using online converters or print-to-PDF)
2. Upload the PDF version instead
3. PDF and DOCX processing works without additional software

## Current Status

- ✅ PDF processing: Working
- ✅ DOCX processing: Working  
- ⚠️ Image processing: Requires Tesseract OCR installation

## Troubleshooting

If Tesseract is installed but still not working:
1. Check if it's in PATH: `where tesseract`
2. Manually set path in code if needed
3. Ensure the application has permissions to access Tesseract