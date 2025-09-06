import os
import io
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
import pillow_avif  # noqa: F401 - registers AVIF encoder

from rembg import remove, new_session


def env(key: str, default: str) -> str:
    return os.environ.get(key, default)


STORAGE_DIR = env("BG_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "storage")))
BASE_URL = env("BG_BASE_URL", "http://127.0.0.1:8001")
DEFAULT_MODEL = env("BG_MODEL", "isnet-general-use")
DEVICE = env("BG_DEVICE", "cpu")

os.makedirs(os.path.join(STORAGE_DIR, "images"), exist_ok=True)

app = FastAPI(title="Background Remover")

# CORS: allow dev origins by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/files", StaticFiles(directory=STORAGE_DIR), name="files")


def choose_model(subject: str) -> str:
    subject = (subject or "auto").lower()
    if subject == "person":
        return "u2net_human_seg"
    if subject in ("product", "general"):
        return "isnet-general-use"
    return DEFAULT_MODEL


def encode_image(img: Image.Image, fmt: str, quality: int) -> bytes:
    buf = io.BytesIO()
    fmt = fmt.lower()
    if fmt in ("jpg", "jpeg"):
        img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=max(1, min(quality, 100)))
    elif fmt == "webp":
        img.save(buf, format="WEBP", quality=max(1, min(quality, 100)))
    elif fmt == "avif":
        img.save(buf, format="AVIF", quality=max(1, min(quality, 100)))
    else:
        # PNG default preserves alpha
        img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@app.post("/remove-background")
async def remove_background(
    image: UploadFile = File(...),
    format: str = Form("png"),
    quality: int = Form(95),
    subject: str = Form("auto"),
):
    try:
        raw = await image.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty upload")

        # Prepare model session
        model_name = choose_model(subject)
        session = new_session(model_name=model_name, providers=["CPUExecutionProvider" if DEVICE == "cpu" else "CUDAExecutionProvider"])  # type: ignore

        # Remove background
        out = remove(raw, session=session, alpha_matting=False, post_process_mask=True)

        # Load into PIL
        cut = Image.open(io.BytesIO(out)).convert("RGBA")

        # Encode into requested format
        fmt = (format or "png").lower()
        ext = "jpeg" if fmt == "jpg" else fmt
        bin_data = encode_image(cut, ext, int(quality or 95))

        # Save and return URL
        fname = f"{uuid.uuid4().hex}.{ 'jpg' if ext=='jpeg' else ext }"
        rel_path = os.path.join("images", fname)
        abs_path = os.path.join(STORAGE_DIR, rel_path)
        with open(abs_path, "wb") as f:
            f.write(bin_data)

        url = f"{BASE_URL.rstrip('/')}/files/{rel_path}"
        return {"ok": True, "format": ext, "url": url, "engine": "rembg", "model": model_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove background: {e}")


@app.get("/health")
async def health():
    return {"ok": True}

