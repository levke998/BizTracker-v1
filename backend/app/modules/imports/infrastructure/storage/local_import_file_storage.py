"""Local filesystem storage for uploaded import files."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.modules.imports.application.commands.upload_import_file import (
    StoredImportFile,
)


class LocalImportFileStorage:
    """Stores uploaded files under a local directory."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def store(self, upload: UploadFile) -> StoredImportFile:
        self._root_dir.mkdir(parents=True, exist_ok=True)

        original_name = upload.filename or "upload.bin"
        suffix = Path(original_name).suffix
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        target_path = self._root_dir / safe_name

        upload.file.seek(0)
        with target_path.open("wb") as file_object:
            shutil.copyfileobj(upload.file, file_object)

        return StoredImportFile(
            original_name=original_name,
            stored_path=str(target_path.resolve()),
            mime_type=upload.content_type,
            size_bytes=target_path.stat().st_size,
        )
