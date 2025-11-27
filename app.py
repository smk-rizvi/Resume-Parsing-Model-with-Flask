# FLASK APP - Run the app using flask --app app.py run
import os, sys
from flask import Flask, request, render_template
from pypdf import PdfReader 
import json
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
UPLOAD_PATH = r"__DATA__"

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH)

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
        
        # Check if file is selected
        if doc.filename == '':
            return render_template('index.html', error="No file selected")
        
        # Save and process the file
        doc.save(os.path.join(UPLOAD_PATH, "file.pdf"))
        doc_path = os.path.join(UPLOAD_PATH, "file.pdf")
        data = _read_file_from_path(doc_path)
        
        # Pass the key to the function
        data = ats_extractor(data, groq_api_key)
        
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
 
def _read_file_from_path(path):
    reader = PdfReader(path) 
    data = ""

    for page_no in range(len(reader.pages)):
        page = reader.pages[page_no] 
        data += page.extract_text()

    return data 


if __name__ == "__main__":
    app.run(port=8000, debug=True)

