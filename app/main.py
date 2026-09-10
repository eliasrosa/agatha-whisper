"""AgathaWhisper — microserviço STT (speech-to-text) do homelab.

Recebe um arquivo de áudio, transcreve com faster-whisper (CTranslate2, CPU),
e devolve o texto. Irmão do LunaSpeak (que é o TTS): aqui é a direção inversa,
áudio -> texto. Serviço apartado e reutilizável (o Kiro Crew, o IDE, ou qualquer
cliente apontam pra cá em vez de cada um embutir o próprio whisper).
"""
import logging
import os
import tempfile
import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

# --- observabilidade ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("agathawhisper")

# --- config (env) ---
# Modelo do faster-whisper: tiny/base/small/medium/large-v3/large-v3-turbo.
# 'small' é o melhor equilíbrio pt-BR em CPU; 'large-v3-turbo' é mais preciso e pesado.
MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
# device cpu|cuda; compute_type int8 (CPU) é rápido e leve. auto deixa a lib decidir.
DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
# idioma fixo evita autodetecção errada em áudio curto; vazio = autodetecta.
LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "pt") or None
# onde o modelo é cacheado (volume, pra não rebaixar a cada restart)
MODEL_DIR = os.environ.get("MODEL_DIR", "/models")
# teto de tamanho do upload (MB) — evita abuso/OOM
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "25"))

app = FastAPI(title="AgathaWhisper", version="0.1.0")

_model = None  # carregado preguiçosamente no primeiro /transcribe


def _get_model():
    """Carrega o modelo uma vez (lazy). O download acontece aqui no 1º uso."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel  # import tardio: só quando usado
        log.info("carregando modelo whisper size=%s device=%s compute=%s", MODEL_SIZE, DEVICE, COMPUTE_TYPE)
        _model = WhisperModel(
            MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=MODEL_DIR
        )
        log.info("modelo carregado")
    return _model


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str | None = Form(default=None),
):
    """Recebe um arquivo de áudio (multipart) e devolve o texto transcrito.

    Campos:
      - audio: o arquivo (ogg/opus, mp3, wav, m4a... o ffmpeg do faster-whisper decodifica)
      - language: opcional, sobrescreve o WHISPER_LANGUAGE do serviço (ex. 'pt', 'en')

    Retorna: {ok, text, language, duration_ms, model}
    """
    started = time.perf_counter()
    raw = await audio.read()
    if not raw:
        raise HTTPException(400, "audio vazio")
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, {"ok": False, "reason": "too_large", "limit_mb": MAX_UPLOAD_MB})

    lang = language or LANGUAGE
    suffix = os.path.splitext(audio.filename or "")[1] or ".bin"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(raw)
        tmp.flush()
        tmp.close()
        model = _get_model()
        segments, info = model.transcribe(tmp.name, language=lang, vad_filter=True)
        text = "".join(seg.text for seg in segments).strip()
        dur = round((time.perf_counter() - started) * 1000)
        log.info(
            "transcribe ok lang=%s chars=%d duration_ms=%d bytes=%d",
            info.language, len(text), dur, len(raw),
        )
        return {
            "ok": True,
            "text": text,
            "language": info.language,
            "duration_ms": dur,
            "model": MODEL_SIZE,
        }
    except Exception:
        log.exception("transcribe erro duration_ms=%d", round((time.perf_counter() - started) * 1000))
        raise HTTPException(500, "falha na transcricao")
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": MODEL_SIZE,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "language": LANGUAGE or "auto",
        "model_loaded": _model is not None,
        "max_upload_mb": MAX_UPLOAD_MB,
    }
