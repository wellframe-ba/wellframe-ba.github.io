#!/usr/bin/env python3
"""Email collector with GCS backend + static file serving"""

import os
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

app = FastAPI()

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET", "")
GCS_FILE = "subscribers.json"

STATIC_DIR = Path("/usr/share/nginx/html")

try:
    from google.cloud import storage
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    gcs_available = True
except Exception as e:
    print(f"Warning: GCS not available: {e}")
    client = None
    bucket = None
    gcs_available = False

def read_subscribers():
    if not gcs_available or bucket is None:
        return []
    try:
        blob = bucket.blob(GCS_FILE)
        if not blob.exists():
            return []
        content = blob.download_as_bytes().decode('utf-8')
        return json.loads(content) if content else []
    except Exception as e:
        print(f"Error reading from GCS: {e}")
        return []

def write_subscribers(subscribers):
    if not gcs_available or bucket is None:
        return False
    try:
        blob = bucket.blob(GCS_FILE)
        blob.upload_from_string(json.dumps(subscribers, indent=2))
        return True
    except Exception as e:
        print(f"Error writing to GCS: {e}")
        return False

@app.get("/health")
async def health():
    return {"status": "ok", "gcs_available": gcs_available}

@app.post("/api/signup")
async def signup(email: str = Form(...)):
    subscribers = read_subscribers()
    email_lower = email.lower().strip()

    for sub in subscribers:
        if sub["email"] == email_lower:
            return JSONResponse(
                content={"status": "exists", "message": "Email already registered"},
                status_code=400
            )

    subscribers.append({
        "email": email_lower,
        "timestamp": datetime.utcnow().isoformat()
    })

    success = write_subscribers(subscribers)
    if not success:
        return JSONResponse(
            content={"status": "error", "message": "Failed to save email"},
            status_code=500
        )

    return {"status": "success", "message": "Email collected"}

@app.get("/api/subscribers")
async def get_subscribers():
    return JSONResponse(content=read_subscribers())

@app.get("/{filename}")
async def serve_file(filename: str):
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
    file_path = STATIC_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # Fallback to index.html for SPA-style routing
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="index.html not found")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)