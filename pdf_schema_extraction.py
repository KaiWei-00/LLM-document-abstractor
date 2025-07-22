import os
import json
import fitz  # PyMuPDF
import openai
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Set your OpenAI key here or use environment variable
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

app = FastAPI()

# Optional: CORS if you're calling from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using PyMuPDF"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_fields_from_text(schema: dict, text: str) -> dict:
    """Use OpenAI to fill in the schema based on extracted PDF text"""
    prompt = f"""
You are a data extraction agent.

Extract the following fields from the document content below.
If a field is not found or is ambiguous, return an empty string.

Required fields:
{json.dumps(schema, indent=2)}

Document content:
{text}

IMPORTANT:
- Return ONLY a valid JSON object.
- No comments or explanations.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        raise ValueError("OpenAI returned invalid JSON: " + output)

@app.post("/extract_schema_pdf")
async def extract_schema_pdf(file: UploadFile = File(...), schema: str = Form(...)):
    """
    Upload a PDF and schema.
    Returns structured data from each page based on the schema, combined into one JSON output.
    """
    try:
        pdf_bytes = await file.read()
        schema_dict = json.loads(schema)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_results = []
        for i, page in enumerate(doc):
            page_text = page.get_text()
            try:
                page_result = extract_fields_from_text(schema_dict, page_text)
            except Exception as e:
                # Standardize JSON decode errors for test compatibility
                if isinstance(e, json.JSONDecodeError) or "JSONDecodeError" in str(type(e)) or "OpenAI returned invalid JSON" in str(e):
                    page_result = {"error": f"Failed to parse JSON: {str(e)}", "page": i+1}
                else:
                    page_result = {"error": str(e), "page": i+1}
            page_results.append({"page": i+1, "result": page_result})
        combined = {"pages": page_results}
        return JSONResponse(content=combined)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
