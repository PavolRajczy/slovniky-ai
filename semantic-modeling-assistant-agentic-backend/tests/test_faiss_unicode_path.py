"""FAISS index files can be stored under a folder name with diacritics."""
import os
import sys

import faiss

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_base_index.faiss_paths import read_faiss_index, write_faiss_index


def test_roundtrip_under_a_unicode_directory(tmp_path):
    folder = tmp_path / "ETČ Metodická pravidla"
    index = faiss.IndexFlatIP(4)
    destination = folder / "faiss.index"

    write_faiss_index(index, destination)
    loaded = read_faiss_index(destination)

    assert destination.is_file()
    assert loaded.d == 4
    assert loaded.ntotal == 0
