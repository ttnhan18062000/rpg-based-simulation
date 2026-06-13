FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch first — prevents pip from resolving the default CUDA wheel
# (default torch wheel is ~2 GB; CPU-only is ~250 MB)
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining deps (sentence-transformers will reuse the already-installed torch)
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.0.0" \
    "sentence-transformers>=2.7.0" \
    "sqlite-vec>=0.1.1" \
    "rank-bm25>=0.2.2"

# Pre-download the embedding model (baked into image layer, avoids runtime download)
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code (only the tools needed for the server)
COPY tools/knowledge_search.py tools/knowledge_search.py
COPY tools/search_server.py tools/search_server.py

EXPOSE 8765

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8765/api/health')" || exit 1

CMD ["uvicorn", "tools.search_server:app", "--host", "0.0.0.0", "--port", "8765"]
