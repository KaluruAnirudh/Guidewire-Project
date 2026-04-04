import os
from datetime import datetime
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename


def save_uploaded_files(files):
    if not files:
        return []

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    uploaded_files = []

    for file in files:
        if not file or not file.filename:
            continue

        extension = os.path.splitext(file.filename)[1].lower()
        safe_name = secure_filename(f"{datetime.utcnow():%Y%m%d%H%M%S}_{uuid4().hex}{extension}")
        absolute_path = os.path.join(upload_dir, safe_name)
        file.save(absolute_path)

        uploaded_files.append(
            {
                "original_name": file.filename,
                "stored_name": safe_name,
                "path": absolute_path,
                "mime_type": file.mimetype,
                "size_bytes": os.path.getsize(absolute_path),
            }
        )

    return uploaded_files

