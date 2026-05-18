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
SUBSCRIBERS_FILE = "subscribers.json"
BOOKINGS_FILE = "bookings.json"

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

def read_json_file(filename):
    if not gcs_available or bucket is None:
        return []
    try:
        blob = bucket.blob(filename)
        if not blob.exists():
            return []
        content = blob.download_as_bytes().decode('utf-8')
        return json.loads(content) if content else []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

def write_json_file(filename, data):
    if not gcs_available or bucket is None:
        return False
    try:
        blob = bucket.blob(filename)
        blob.upload_from_string(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"Error writing {filename}: {e}")
        return False

def read_subscribers():
    return read_json_file(SUBSCRIBERS_FILE)

def write_subscribers(subscribers):
    return write_json_file(SUBSCRIBERS_FILE, subscribers)

def read_bookings():
    return read_json_file(BOOKINGS_FILE)

def write_bookings(bookings):
    return write_json_file(BOOKINGS_FILE, bookings)

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

@app.delete("/api/subscribers/{email}")
async def delete_subscriber(email: str):
    subscribers = read_subscribers()
    email_lower = email.lower().strip()
    original_len = len(subscribers)
    subscribers = [s for s in subscribers if s["email"] != email_lower]
    if len(subscribers) == original_len:
        return JSONResponse(content={"status": "error", "message": "Subscriber not found"}, status_code=404)
    success = write_subscribers(subscribers)
    if not success:
        return JSONResponse(content={"status": "error", "message": "Failed to delete subscriber"}, status_code=500)
    return {"status": "success", "message": "Subscriber deleted"}

@app.post("/api/book-call")
async def book_call(
    name: str = Form(...),
    company: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    operation_type: str = Form(""),
    pain_point: str = Form(""),
    infrastructure: str = Form(""),
    budget: str = Form("")
):
    bookings = read_bookings()

    booking = {
        "id": f"bk_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(bookings) + 1}",
        "name": name,
        "company": company,
        "email": email.lower().strip(),
        "phone": phone,
        "operation_type": operation_type,
        "pain_point": pain_point,
        "infrastructure": infrastructure,
        "budget": budget,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "new",
        "notes": ""
    }

    bookings.append(booking)
    success = write_bookings(bookings)

    if not success:
        return JSONResponse(
            content={"status": "error", "message": "Failed to save booking"},
            status_code=500
        )

    return {"status": "success", "message": "Booking received"}

@app.get("/api/bookings")
async def get_bookings():
    return JSONResponse(content=read_bookings())

@app.put("/api/bookings/{booking_id}")
async def update_booking(booking_id: str, status: str = Form(""), notes: str = Form("")):
    bookings = read_bookings()
    booking = next((b for b in bookings if b.get("id") == booking_id), None)
    if not booking:
        return JSONResponse(content={"status": "error", "message": "Booking not found"}, status_code=404)
    if status:
        booking["status"] = status
    if notes is not None:
        booking["notes"] = notes
    success = write_bookings(bookings)
    if not success:
        return JSONResponse(content={"status": "error", "message": "Failed to update booking"}, status_code=500)
    return {"status": "success", "message": "Booking updated"}

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