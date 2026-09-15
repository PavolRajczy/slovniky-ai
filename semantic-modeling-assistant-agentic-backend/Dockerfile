# Semantic Modeling Assistant — agentic backend
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/backend/src \
    # Hugging Face / Docling caches inside the image (or volume if remapped)
    HF_HOME=/opt/backend/.cache/huggingface \
    EASYOCR_MODULE_PATH=/opt/backend/.cache/easyocr

WORKDIR /opt/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# CPU PyTorch first so sentence-transformers / docling do not pull a CUDA wheel.
# pywin32 is Windows-only (environment marker). torch/torchvision come from the CPU index.
RUN python -c "from pathlib import Path; lines=[l for l in Path('requirements.txt').read_text(encoding='utf-8-sig').splitlines() if not l.lower().startswith(('torch==','torchvision==','torch ','torchvision '))]; Path('/tmp/requirements.docker.txt').write_text('\\n'.join(lines)+'\\n', encoding='utf-8')" \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.8.0 torchvision==0.23.0 \
    && pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r /tmp/requirements.docker.txt

COPY src ./src
COPY run_api.py ./run_api.py

RUN mkdir -p \
        data/ontologies \
        data/projects \
        data/knowledge_base/esel \
        data/knowledge_base/local \
        .cache/huggingface \
        .cache/easyocr

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=10 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

# Single worker: FAISS indexes live in process memory.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
