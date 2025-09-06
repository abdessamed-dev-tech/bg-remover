Background Removal API (FastAPI + rembg)

Overview
- Standalone Python service that removes backgrounds using rembg (U²‑Net/ISNet models).
- Saves results to local storage and serves them as static files.
- Simple JSON API compatible with the Vue frontend.

Quick start
1) Python 3.10+
2) Install dependencies:
   pip install -r requirements.txt
3) Run:
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload

Env vars (optional)
- BG_STORAGE_DIR: where to store output files (default: ./storage)
- BG_BASE_URL: public base URL (default: http://127.0.0.1:8001)
- BG_MODEL: isnet-general-use | u2net_human_seg | u2net | u2netp (default: isnet-general-use)
- BG_DEVICE: cpu | cuda (default: cpu)

API
- POST /remove-background
  - multipart form-data: image (file)
  - optional fields: format (png/webp/avif/jpeg), quality (1..100), subject (auto/person/general/product)
  - response: { ok: true, url: "<BASE_URL>/files/<relative_path>" }

