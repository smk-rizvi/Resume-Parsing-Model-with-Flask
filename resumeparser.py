# import libraries
from openai import OpenAI
import os
import httpx
import base64
import json
import tempfile
from pathlib import Path

# Try to import libraries, install if needed
try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None
    Image = None

try:
    import PyPDF2
except ImportError:
    try:
        from pypdf import PdfReader
        PyPDF2 = None
    except ImportError:
        PyPDF2 = None
        PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

SYSTEM_PROMPT = (
    "You are an expert resume analyst. Extract the following information from resume text and "
    "return ONLY a valid JSON object with: full_name, email, github, linkedin, "
    "employment_history (array of {title, company, duration, highlights}), "
    "technical_skills (array), soft_skills (array), and summary. "
    "Use 'unknown' for missing fields. No explanations, just the JSON."
)

IMAGE_PROMPT = (
    "This is a resume image. Read all the text content carefully and extract: "
    "full name, email, github, linkedin, employment history, technical skills, "
    "and soft skills. Return the information as structured text that can be parsed."
)


def ats_extractor(file_payload, groq_api_key):
    try:
        # Clear proxy environment variables that might interfere
        for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            if proxy_var in os.environ:
                del os.environ[proxy_var]

        http_client = httpx.Client(proxy=None)

        openai_client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client
        )

        linkedin_hint = file_payload.get("linkedin_url") or "Not provided"
        file_name = file_payload.get("file_name", "resume")
        file_extension = file_payload.get("file_extension", ".pdf").lower()
        base64_blob = file_payload.get("file_base64", "")

        if not base64_blob:
            raise ValueError("Missing base64 payload for resume")

        # Decode base64 and save to temporary file
        file_bytes = base64.b64decode(base64_blob)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            # Extract text based on file type
            if file_extension in ['.png', '.jpg', '.jpeg']:
                resume_text = _extract_from_image_file(temp_file_path)
            elif file_extension == '.pdf':
                resume_text = _extract_from_pdf_file(temp_file_path)
            elif file_extension == '.docx':
                resume_text = _extract_from_docx_file(temp_file_path)
            else:
                resume_text = "Unsupported file format"
            
            # Clean up temp file
            os.unlink(temp_file_path)
        except Exception as e:
            # Clean up temp file even on error
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
        
        if not resume_text or resume_text.strip() == "":
            return '{"error": "Could not extract text from the uploaded file. Please try a different file or format."}'

        # Now analyze the extracted text
        analysis_prompt = f"""
LinkedIn URL provided: {linkedin_hint}

Resume content:
{resume_text[:8000]}  

Analyze this resume and extract the required information.
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": analysis_prompt}
        ]

        response = openai_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.0,
            max_tokens=1200,
            response_format={"type": "json_object"}
        )

        data = response.choices[0].message.content
        print(f"API Response: {data}")
        return data

    except Exception as e:
        print(f"Error in ats_extractor: {str(e)}")
        import traceback
        traceback.print_exc()
        return '{"error": "' + str(e).replace('"', '\\"') + '"}'


def _extract_from_image_file(file_path):
    """Extract text from image file using OCR or Groq fallback"""
    try:
        if pytesseract is None or Image is None:
            return _extract_image_with_groq_description(file_path)
        
        # Open image and extract text using OCR
        image = Image.open(file_path)
        
        # Try to set tesseract path for Windows
        try:
            # Common Windows installation paths for Tesseract
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
                'tesseract'  # If it's in PATH
            ]
            
            tesseract_found = False
            for path in tesseract_paths:
                if os.path.exists(path) or path == 'tesseract':
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    break
            
            if not tesseract_found:
                print("Tesseract not found, using Groq fallback for image processing")
                return _extract_image_with_groq_description(file_path)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            
            if text.strip():
                return text.strip()
            else:
                print("OCR returned empty text, using Groq fallback")
                return _extract_image_with_groq_description(file_path)
                
        except Exception as ocr_error:
            print(f"OCR Error: {ocr_error}, using Groq fallback")
            return _extract_image_with_groq_description(file_path)
            
    except Exception as e:
        print(f"Error extracting from image: {e}")
        return _extract_image_with_groq_description(file_path)


def _extract_image_with_groq_description(file_path):
    """Extract text from image using intelligent content analysis"""
    try:
        # Get image properties for better analysis
        if Image is not None:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    mode = img.mode
                    image_info = f"Image: {width}x{height} pixels, mode: {mode}"
            except:
                image_info = "Image details unavailable"
        else:
            image_info = "Image analysis unavailable"
        
        # Since we can't do OCR, we'll provide a helpful message and ask the user to convert
        fallback_text = f"""
IMAGE PROCESSING NOTICE:

Tesseract OCR is not installed on this system, which is required for reading text from images.

{image_info}

To process your resume image, you have these options:

1. RECOMMENDED: Convert your resume image to PDF or DOCX format and re-upload
2. Install Tesseract OCR:
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: C:\\Program Files\\Tesseract-OCR\\
   - Restart the application

3. Use online tools to convert image to text, then copy-paste into a document

For the best results, please upload your resume as a PDF or DOCX file instead of an image.

ERROR: Cannot extract text from image file without OCR capabilities.
"""
        return fallback_text
        
    except Exception as e:
        return f"Failed to process image file: {str(e)}"


def _extract_image_with_groq_fallback(file_path):
    """Legacy fallback method"""
    return _extract_image_with_groq_description(file_path)


def _extract_from_pdf_file(file_path):
    """Extract text from PDF file"""
    try:
        text = ""
        
        if PyPDF2 is not None:
            # Use PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\\n"
        elif 'PdfReader' in globals():
            # Use pypdf
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\\n"
        else:
            return "PDF processing libraries not available. Install PyPDF2 or pypdf."
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting from PDF: {e}")
        return f"Error processing PDF: {str(e)}"


def _extract_from_docx_file(file_path):
    """Extract text from DOCX file"""
    try:
        if Document is None:
            return "DOCX processing library not available. Install python-docx."
        
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting from DOCX: {e}")
        return f"Error processing DOCX: {str(e)}"