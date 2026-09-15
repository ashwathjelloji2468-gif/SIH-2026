import os
import zipfile
import shutil
from typing import List, Dict, Any, Optional

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024       # 50 MB
MAX_EXTRACTED_BYTES = 250 * 1024 * 1024   # 250 MB
MAX_EXTRACTED_FILES = 2000                 # 2,000 files
MAX_SINGLE_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

class SecurityExtractionError(ValueError):
    """Raised when archive extraction violates security boundary or size limits."""
    pass

# Alias for backwards compatibility / test import
ZipSecurityException = SecurityExtractionError

def is_safe_path(target_dir: str, dest_path: str) -> bool:
    r"""
    Verifies that dest_path resolves strictly inside target_dir.
    Prevents path traversal attacks (e.g. ../../outside.txt, absolute paths, C:\outside.txt).
    """
    abs_target = os.path.realpath(target_dir)
    abs_dest = os.path.realpath(dest_path)
    return abs_dest.startswith(abs_target + os.sep) or abs_dest == abs_target

def extract_zip_safely(
    zip_path_or_file,
    destination_dir: str,
    max_extracted_bytes: int = MAX_EXTRACTED_BYTES,
    max_extracted_files: int = MAX_EXTRACTED_FILES,
    max_single_file_bytes: int = MAX_SINGLE_FILE_BYTES
) -> List[str]:
    """
    Safely extracts a ZIP archive into destination_dir while protecting against:
    1. Zip slip / path traversal (../, ..\\, absolute paths)
    2. Symlink escape attacks
    3. Zip bomb / resource exhaustion (file count & byte size limits)
    
    If any entry violates policy, extraction aborts immediately and cleans up destination_dir.
    Returns list of extracted relative file paths.
    """
    os.makedirs(destination_dir, exist_ok=True)
    destination_dir_abs = os.path.realpath(destination_dir)

    extracted_files: List[str] = []
    total_bytes_extracted = 0

    try:
        with zipfile.ZipFile(zip_path_or_file, 'r') as zf:
            infolist = zf.infolist()

            if len(infolist) > max_extracted_files:
                raise SecurityExtractionError(
                    f"Archive file count ({len(infolist)}) exceeds maximum allowed limit ({max_extracted_files})."
                )

            for member in infolist:
                filename = member.filename
                
                # Reject suspicious encodings or empty names
                if not filename or '\0' in filename:
                    raise SecurityExtractionError("Archive entry contains invalid or null byte characters.")

                # Construct target destination path
                target_path = os.path.join(destination_dir_abs, filename)

                # Security Rule 1: Path Traversal check
                if not is_safe_path(destination_dir_abs, target_path):
                    raise SecurityExtractionError(
                        f"Zip Slip Traversal Blocked: Archive entry '{filename}' attempts to write outside target root."
                    )

                # Security Rule 2: Symlink Escape check (POSIX mode 0120000 indicates symlink)
                is_symlink = (member.external_attr >> 16) & 0o120000 == 0o120000
                if is_symlink:
                    # Reject symlinks in extracted user archives to prevent host file disclosure
                    raise SecurityExtractionError(
                        f"Symlink Security Policy: Symlink entry '{filename}' is not permitted in repository archives."
                    )

                # Skip directories (they will be created automatically if needed)
                if member.is_dir() or filename.endswith('/') or filename.endswith('\\'):
                    os.makedirs(target_path, exist_ok=True)
                    continue

                # Security Rule 3: Single file size check
                if member.file_size > max_single_file_bytes:
                    raise SecurityExtractionError(
                        f"Oversized File Entry: Entry '{filename}' ({member.file_size} bytes) exceeds single file limit ({max_single_file_bytes} bytes)."
                    )

                # Security Rule 4: Total extracted bytes limit check
                total_bytes_extracted += member.file_size
                if total_bytes_extracted > max_extracted_bytes:
                    raise SecurityExtractionError(
                        f"Extracted Byte Limit Exceeded: Total extracted size exceeds limit of {max_extracted_bytes} bytes."
                    )

                # Create parent directories safely
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                # Controlled streaming write
                with zf.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)

                extracted_files.append(os.path.relpath(target_path, destination_dir_abs))

    except Exception as e:
        # Clean up any partially extracted files on failure
        if os.path.exists(destination_dir_abs):
            shutil.rmtree(destination_dir_abs, ignore_errors=True)
        if isinstance(e, SecurityExtractionError):
            raise
        raise SecurityExtractionError(f"Failed to extract ZIP archive safely: {str(e)}")

    return extracted_files
