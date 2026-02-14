import os
import re
import json
import logging
import time as import_time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pdfplumber
import docx
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "cet6document")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
VOCAB_FILE = os.path.join(BACKEND_DIR, "vocabulary.json")
ANNOTATIONS_DIR = os.path.join(DATA_DIR, "annotations")
ESSAYS_DIR = os.path.join(DATA_DIR, "essays")

# Ensure data directories exist
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)
os.makedirs(ESSAYS_DIR, exist_ok=True)

# --- Models ---
class VocabularyItem(BaseModel):
    id: Optional[str] = None
    text: str
    phonetic: Optional[str] = ""
    meaning: Optional[str] = ""
    addedAt: Optional[int] = None

class AddVocabularyRequest(BaseModel):
    word: str

class AnnotationData(BaseModel):
    docId: str
    strokes: List[dict] # Simplified typing, actually complex objects

class EssayData(BaseModel):
    docId: str
    content: str

# --- Helpers ---
def fetch_word_info(word: str) -> dict:
    """Fetch word definition from Youdao Suggest API"""
    try:
        url = f"http://dict.youdao.com/suggest?num=1&doctype=json&q={word}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and "entries" in data["data"] and len(data["data"]["entries"]) > 0:
                entry = data["data"]["entries"][0]
                return {
                    "meaning": entry.get("explain", ""),
                    "phonetic": "" # Suggest API doesn't always provide phonetic easily, needed extra parsing?
                    # Actually suggest API just gives explain.
                    # For better data, we might need full API, but let's start with explain.
                }
    except Exception as e:
        logger.error(f"Error fetching word info for {word}: {e}")
    
    return {"meaning": f"Meaning of {word} (Fetch failed)", "phonetic": ""}

def load_vocabulary():
    if not os.path.exists(VOCAB_FILE):
        return []
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_vocabulary(items):
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def smart_merge_lines(raw_lines: List[str]) -> List[str]:
    """
    Intelligently merge lines that are split by PDF layout.
    """
    if not raw_lines:
        return []

    merged_lines = []
    current_line = ""

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        if not current_line:
            current_line = line
            continue

        # Check for list items or specific patterns that should always be on a new line
        # e.g. "1.", "A)", "Section A"
        is_list_item = re.match(r'^(\d+\.|[A-Z]\)|Section|Part|Item)', line)
        
        # Check if previous line ends with sentence terminator
        prev_ends_sentence = current_line.endswith(('.', '?', '!', ':', '。', '？', '！', '：'))

        # Check for hyphenation (word split)
        if current_line.endswith('-'):
            # Remove verify hyphen and join without space
            current_line = current_line[:-1] + line
        elif not is_list_item and not prev_ends_sentence:
             # Merge with space
            current_line += " " + line
        else:
            # Push current and start new
            merged_lines.append(current_line)
            current_line = line
    
    if current_line:
        merged_lines.append(current_line)
        
    return merged_lines

def get_safe_id_path(doc_id: str):
    """Sanitize doc_id to be safe for filenames"""
    # Create a hashed or sanitized filename from the doc path to avoid deep nesting issues in data dir
    import hashlib
    # We use a hash of the doc_id (which is a path) to store metadata flatly
    # or we could mirror structure. Flat hash is easier for now to avoid 'mkdir -p' logic for every file.
    safe_name = hashlib.md5(doc_id.encode('utf-8')).hexdigest()
    return safe_name

def extract_pdf_lines(path):
    lines = [] # Collect all lines from all pages
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split('\n'))
        
        # Apply smart merge
        processed_lines = smart_merge_lines(lines)
        return processed_lines
            
    except Exception as e:
        logger.error(f"Error reading PDF {path}: {e}")
        return ["Error reading PDF file."]

def extract_docx_lines(path):
    lines = []
    try:
        doc = docx.Document(path)
        for para in doc.paragraphs:
            if para.text.strip():
                lines.append(para.text)
    except Exception as e:
        logger.error(f"Error reading DOCX {path}: {e}")
        lines = ["Error reading DOCX file."]
    return lines

# --- Routes ---

@app.get("/api/v1/documents/list")
async def get_documents_list():
    data = {}
    for root, dirs, files in os.walk(DOCS_DIR):
        match = re.search(r"(\d{4})年(\d{2})月CET6真题", os.path.basename(root))
        if match:
            year, month = match.groups()
            section_key = f"{year}-{month}"
            if section_key not in data:
                data[section_key] = {"year": year, "month": month, "papers": []}
            
            for file in files:
                if file.lower().endswith(('.pdf', '.docx', '.doc')):
                    title = os.path.splitext(file)[0]
                    # Create a relative path from DOCS_DIR
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, DOCS_DIR).replace("\\", "/")
                    
                    data[section_key]["papers"].append({
                        "id": rel_path,
                        "title": title,
                        "filename": file
                    })
    
    result = list(data.values())
    result.sort(key=lambda x: (x["year"], x["month"]), reverse=True)
    return {"code": 200, "data": result}

@app.get("/api/v1/documents/content")
async def get_document_content(doc_id: str):
    # doc_id is relative path inside cet6document
    # Security check: prevent directory traversal
    safe_path = os.path.normpath(os.path.join(DOCS_DIR, doc_id))
    if not safe_path.startswith(os.path.abspath(DOCS_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    lines = []
    if safe_path.lower().endswith(".pdf"):
        lines = extract_pdf_lines(safe_path)
    elif safe_path.lower().endswith(".docx"):
        lines = extract_docx_lines(safe_path)
    else:
        lines = ["Unsupported file format"]

    return {
        "code": 200, 
        "data": {
            "docId": doc_id,
            "title": os.path.basename(doc_id),
            "lines": lines,
            "meta": {"totalPages": 0} # Placeholder
        }
    }

@app.get("/api/v1/user/annotations")
async def get_annotations(doc_id: str):
    file_id = get_safe_id_path(doc_id)
    file_path = os.path.join(ANNOTATIONS_DIR, f"{file_id}.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {"code": 200, "data": data}
        except Exception as e:
            logger.error(f"Failed to load annotation {doc_id}: {e}")
            return {"code": 500, "message": "Error loading annotations"}
    
    return {"code": 200, "data": []}

@app.post("/api/v1/user/annotations")
async def save_annotations(payload: AnnotationData):
    file_id = get_safe_id_path(payload.docId)
    file_path = os.path.join(ANNOTATIONS_DIR, f"{file_id}.json")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload.strokes, f)
        return {"code": 200, "message": "Saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save annotation {payload.docId}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save")

@app.get("/api/v1/user/essay")
async def get_essay(doc_id: str):
    file_id = get_safe_id_path(doc_id)
    file_path = os.path.join(ESSAYS_DIR, f"{file_id}.md")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                return {"code": 200, "data": {"content": content}}
        except Exception as e:
            logger.error(f"Failed to load essay {doc_id}: {e}")
            return {"code": 500, "message": "Error loading essay"}
            
    return {"code": 200, "data": {"content": ""}}

@app.post("/api/v1/user/essay")
async def save_essay(payload: EssayData):
    file_id = get_safe_id_path(payload.docId)
    file_path = os.path.join(ESSAYS_DIR, f"{file_id}.md")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload.content)
        return {"code": 200, "message": "Saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save essay {payload.docId}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save")

@app.get("/api/v1/user/vocabulary")
async def get_vocabulary(page: int = 1, limit: int = 100):
    items = load_vocabulary()
    # Pagination (simple)
    start = (page - 1) * limit
    end = start + limit
    return {
        "code": 200,
        "data": {
            "total": len(items),
            "items": items[start:end]
        }
    }

@app.post("/api/v1/user/vocabulary")
async def add_vocabulary(req: AddVocabularyRequest):
    items = load_vocabulary()
    # Check duplicate
    if any(item['text'].lower() == req.word.lower() for item in items):
         return {"code": 200, "message": "Already exists", "data": next(i for i in items if i['text'].lower() == req.word.lower())}

    # Fetch info
    info = fetch_word_info(req.word)

    new_item = {
        "id": f"wd_{int(import_time.time() * 1000)}",
        "text": req.word,
        "phonetic": info.get("phonetic", ""),
        "meaning": info.get("meaning", f"Meaning of {req.word}"),
        "addedAt": int(import_time.time() * 1000)
    }
    items.insert(0, new_item) # Add to top
    save_vocabulary(items)
    return {"code": 200, "message": "Added successfully", "data": new_item}

@app.delete("/api/v1/user/vocabulary/{id}")
async def delete_vocabulary(id: str):
    items = load_vocabulary()
    items = [i for i in items if i["id"] != id]
    save_vocabulary(items)
    return {"code": 200, "message": "Deleted successfully"}

# Dictionary lookup (mock)
@app.get("/api/v1/dictionary/lookup")
async def dictionary_lookup(word: str):
    info = fetch_word_info(word)
    return {
        "code": 200,
        "data": {
            "word": word,
            "phonetic": info.get("phonetic", ""),
            "meaning": info.get("meaning", f"Definition of {word}"),
            "examples": []
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
