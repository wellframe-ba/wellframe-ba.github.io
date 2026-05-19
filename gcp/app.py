#!/usr/bin/env python3
"""Email collector with GCS backend + static file serving"""

import os
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Header
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    print("Warning: bcrypt not available, password hashing disabled")

app = FastAPI()

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET", "")
SUBSCRIBERS_FILE = "subscribers.json"
BOOKINGS_FILE = "bookings.json"
CREDENTIALS_FILE = "credentials.json"
SESSION_FILE = "sessions.json"
STATIC_DIR = Path("/usr/share/nginx/html")

# In-memory session store: token -> {username, expires_at}
sessions = {}

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


def read_credentials():
    return read_json_file(CREDENTIALS_FILE)


def read_sessions():
    data = read_json_file(SESSION_FILE)
    # Re-hydrate into memory
    sessions.clear()
    if isinstance(data, list):
        for s in data:
            if isinstance(s, dict) and "token" in s and "expires_at" in s:
                try:
                    sessions[s["token"]] = {
                        "username": s.get("username", ""),
                        "expires_at": datetime.fromisoformat(s["expires_at"])
                    }
                except Exception:
                    pass


def write_sessions():
    data = [
        {"token": token, "username": info["username"], "expires_at": info["expires_at"].isoformat()}
        for token, info in sessions.items()
    ]
    write_json_file(SESSION_FILE, data)


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": username,
        "expires_at": datetime.utcnow() + timedelta(hours=12)
    }
    write_sessions()
    return token


def validate_session(token: str) -> bool:
    if token not in sessions:
        return False
    if datetime.utcnow() > sessions[token]["expires_at"]:
        del sessions[token]
        write_sessions()
        return False
    return True


def get_session_username(token: str) -> str:
    if token not in sessions:
        return None
    if datetime.utcnow() > sessions[token]["expires_at"]:
        del sessions[token]
        write_sessions()
        return None
    return sessions[token]["username"]


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


# ─── Admin Auth ────────────────────────────────────────────────────────────────

@app.post("/api/admin/login")
async def admin_login(username: str = Form(...), password: str = Form(...)):
    if not BCRYPT_AVAILABLE:
        return JSONResponse(content={"status": "error", "message": "Auth unavailable"}, status_code=503)

    credentials = read_credentials()
    for cred in credentials:
        if cred.get("username") == username:
            stored_hash = cred.get("password_hash", "")
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                token = create_session(username)
                return {"status": "success", "token": token, "username": username}
            break

    return JSONResponse(content={"status": "error", "message": "Invalid credentials"}, status_code=401)


@app.post("/api/admin/logout")
async def admin_logout(x_session_token: str = Header(None)):
    if x_session_token and x_session_token in sessions:
        del sessions[x_session_token]
        write_sessions()
    return {"status": "success"}


@app.get("/api/admin/me")
async def admin_me(x_session_token: str = Header(None)):
    if not x_session_token or not validate_session(x_session_token):
        return JSONResponse(content={"status": "error", "message": "Unauthorized"}, status_code=401)
    username = get_session_username(x_session_token)
    return {"status": "success", "username": username}


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