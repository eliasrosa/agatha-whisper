# AgathaWhisper

Microserviço de **transcrição de áudio (STT)** do homelab. Recebe um arquivo de áudio,
transcreve com [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2,
roda bem em CPU) e devolve o texto.

Irmão do **LunaSpeak** (que é o TTS — texto → áudio). Aqui é a direção inversa
(áudio → texto). Serviço **apartado e reutilizável**: em vez de cada instância do Kiro
embutir o próprio whisper, os clientes (Kiro Crew, Kiro IDE/CLI, apps próprios) apontam
para um único endpoint.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/transcribe` | multipart `audio` (arquivo) + `language?` → `{ok, text, language, duration_ms, model}` |
| `GET`  | `/health` | modelo, device, idioma, se o modelo já carregou |

### Exemplo

```bash
curl -sS -X POST http://<HOST>:8094/transcribe \
  -F "audio=@mensagem.ogg" \
  -F "language=pt"
# {"ok":true,"text":"...","language":"pt","duration_ms":1234,"model":"small"}
```

## Config (env)

Ver `.env.example`. Principais: `WHISPER_MODEL` (default `small`), `WHISPER_DEVICE`
(`cpu`), `WHISPER_COMPUTE_TYPE` (`int8`), `WHISPER_LANGUAGE` (`pt`), `MAX_UPLOAD_MB` (25).
Trocar o modelo é editar o `.env` e reiniciar — sem rebuild.

## Rodar

**Dev (porta 8034):**
```bash
docker compose up --build
```

**Prod no ZimaOS (porta 8094):** imagem local, sem registry (padrão LunaSpeak/wallet-app).
```bash
cp .env.example .env
docker compose -f docker-compose-zimaos.yml up -d --build --force-recreate
```

> O modelo é baixado no **primeiro `/transcribe`** e cacheado no volume `agathawhisper_models`
> (não rebaixa a cada restart).

## Notas

- `ffmpeg` está na imagem (decodifica ogg/opus/mp3/m4a antes de transcrever).
- Latência depende do modelo, do áudio e do hardware. Medido em prod (ZimaOS, CPU
  compartilhada, áudio ~4-5s de fala): **cold start** ~68s com `large-v3-turbo` (dominado
  pelo download do modelo ~1.6 GB, uma vez só); **warm** ~12s por transcrição (modelo em
  cache). Adequado a uso **assíncrono** (manda áudio → recebe texto), não a tempo real em CPU.
- **GPU**: rodar em CUDA (`WHISPER_DEVICE=cuda`, `WHISPER_COMPUTE_TYPE=float16`) derruba a
  latência para ~1-3s, mas exige imagem com libs CUDA/cuDNN e runtime `nvidia` no Docker.
  Em VRAM pequena (≤2 GB), preferir um modelo menor (`small`/`base`/`distil`) — o
  `large-v3-turbo` fica no limite.
- Repo pensado para ser **público** — sem IP/host/token no versionado (placeholders `<HOST>`).
  O serviço **não tem credencial** (só recebe áudio e devolve texto).
