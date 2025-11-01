import os
from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil
import uuid

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def save_upload_file_local(file: UploadFile) -> str:
    # Validate size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Validate extension
    ext = Path(file.filename).suffix or ""
    dest_filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / dest_filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"/uploads/{dest_filename}"

# Placeholder for S3 upload (production)
def upload_file_to_s3(file: UploadFile, bucket: str) -> str:
    # implement boto3 upload in production
    return f"https://{bucket}.s3.amazonaws.com/{uuid.uuid4().hex}{Path(file.filename).suffix}"
