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
- Latência depende do modelo e do áudio: `small`/CPU transcreve ~poucos segundos de fala
  em ~1-2s. Modelos maiores (`large-v3-turbo`) são mais precisos e mais lentos.
- Repo pensado para ser **público** — sem IP/host/token no versionado (placeholders `<HOST>`).
