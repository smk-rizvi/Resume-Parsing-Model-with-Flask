# FLASK APP - Run the app using flask --app app.py run
import os, sys, json, base64
from flask import Flask, request, render_template
from dotenv import load_dotenv
from resumeparser import ats_extractor

# NOTE: The .env file must be in the same directory as app.py
load_dotenv()
groq_api_key = os.environ.get("GROQ_API_KEY")

# To check the key immediately, before starting the Flask app
if groq_api_key is None:
    print("FATAL ERROR: GROQ_API_KEY environment variable not set. Please check your .env file.")
    sys.exit(1) # Exit the script if the key is missing

sys.path.insert(0, os.path.abspath(os.getcwd()))

ALLOWED_EXTENSIONS = {
    ".pdf": "PDF document",
    ".docx": "Word document",
    ".png": "PNG image",
    ".jpg": "JPEG image",
    ".jpeg": "JPEG image"
}

MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2 MB limit to keep token usage reasonable

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/process", methods=["POST"])
def ats():
    try:
        # Check if file was uploaded
        if 'pdf_doc' not in request.files:
            return render_template('index.html', error="No file uploaded")
        
        doc = request.files['pdf_doc']
        linkedin_url = request.form.get('linkedin_url', '').strip()
        
        # Check if file is selected
        if doc.filename == '':
            return render_template('index.html', error="No file selected")
        
        extension = os.path.splitext(doc.filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return render_template('index.html', error="Unsupported file type. Please upload PDF, DOCX, PNG, or JPG files.")

        file_bytes = doc.read()
        if not file_bytes:
            return render_template('index.html', error="Uploaded file is empty")

        if len(file_bytes) > MAX_UPLOAD_SIZE:
            return render_template('index.html', error="File too large. Please upload a file smaller than 2 MB.")

        encoded_file = base64.b64encode(file_bytes).decode('utf-8')
        payload = {
            "file_name": doc.filename,
            "file_extension": extension,
            "file_label": ALLOWED_EXTENSIONS[extension],
            "file_base64": encoded_file,
            "linkedin_url": linkedin_url
        }
        
        # Pass the key to the function
        data = ats_extractor(payload, groq_api_key)
        
        # Parse JSON response
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Raw data: {data}")
            return render_template('index.html', error=f"Failed to parse response: {str(e)}")
        
        return render_template('index.html', data=parsed_data)
    
    except Exception as e:
        print(f"Error in /process route: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', error=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    app.run(port=8000, debug=True)

