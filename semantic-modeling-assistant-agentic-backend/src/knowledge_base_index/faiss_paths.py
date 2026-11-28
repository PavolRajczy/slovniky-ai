"""Read and write FAISS files without giving the C++ layer a Unicode path.

faiss.write_index uses fopen. On Windows that call fails for a path whose
name contains diacritics, even when the directory exists.
"""
import os
import tempfile
from pathlib import Path

import faiss


def write_faiss_index(index, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(suffix=".index")
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        faiss.write_index(index, str(temporary_path))
        destination.write_bytes(temporary_path.read_bytes())
    finally:
        temporary_path.unlink(missing_ok=True)


def read_faiss_index(source: Path):
    descriptor, temporary_name = tempfile.mkstemp(suffix=".index")
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        temporary_path.write_bytes(source.read_bytes())
        return faiss.read_index(str(temporary_path))
    finally:
        temporary_path.unlink(missing_ok=True)
