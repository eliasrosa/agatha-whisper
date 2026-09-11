---
inclusion: auto
name: architecture
description: Use quando o usuário perguntar sobre a arquitetura do AgathaWhisper, decisões de design, o fluxo de transcrição, ou a escolha de motor/modelo.
---

# Arquitetura — AgathaWhisper

AgathaWhisper é o microserviço de **STT** (speech-to-text) do homelab: recebe um
arquivo de áudio, transcreve com Whisper e devolve o texto. É o **irmão do LunaSpeak**
(TTS) — a direção inversa. Este documento explica o **porquê** das decisões; para o
*como rodar* veja o `README.md`, para *deploy* veja `deploy.md`.

## Princípio central: STT como serviço, não como biblioteca embutida

O STT do Kiro Crew roda **in-process** (whisper.cpp via `kirocrew[voice]`, dentro do
processo do gateway) — não expõe endpoint, então **não dá pra reaproveitar de fora**.
Cada instância transcreve dentro de si mesma. Quando vários clientes (Kiro Crew, a
ponte Kiro IDE/CLI, apps próprios) precisam de transcrição, embutir um whisper em cada
um é desperdício. A decisão de design do AgathaWhisper é o oposto: **um serviço HTTP
apartado** que qualquer cliente chama por `POST /transcribe`. Mesma topologia do
LunaSpeak pro TTS — desacopla, reutiliza, tira carga do container do agente.

## Fluxo de dados

```
cliente (Kiro Crew / IDE / app)
   │  POST /transcribe  (multipart: audio + language?)
   ▼
AgathaWhisper (FastAPI, app/main.py)
   │  faster-whisper (CTranslate2) — modelo carregado lazy no 1º request
   │  ffmpeg decodifica ogg/opus/mp3/m4a
   ▼
{ok, text, language, duration_ms, model}
```

## Escolha de motor e modelo (e o trade-off)

- **Motor: faster-whisper** (CTranslate2), não whisper.cpp. Motivo: é a implementação
  padrão pra serviço Python standalone, roda bem em CPU (int8) e suporta GPU (CUDA)
  sem trocar de código — só muda `WHISPER_DEVICE`/`WHISPER_COMPUTE_TYPE`. O
  `kirocrew[voice]` (whisper.cpp) é interno do Crew, não serve pra serviço apartado.
- **Modelo: env-driven** (`WHISPER_MODEL`). `small` = equilíbrio pt-BR/CPU;
  `large-v3-turbo` = mais preciso (é o mesmo modelo do STT do Crew), porém mais pesado.
  Trocar o modelo é editar o `.env` e reiniciar — **sem rebuild**. O modelo é baixado
  no **1º `/transcribe`** e cacheado num volume (`MODEL_DIR`), então sobrevive a restart.

## Carga preguiçosa (lazy) do modelo

O modelo NÃO carrega no boot — carrega no **primeiro `/transcribe`** (`_get_model()`,
singleton). Consequência: o 1º request é lento (inclui download + load); os seguintes
usam o modelo em memória/cache. O `/health` expõe `model_loaded` pra distinguir os dois
estados sem efeito colateral (não força o load).

## Latência (medida em prod, CPU compartilhada no ZimaOS)

- Cold start: ~68s com `large-v3-turbo` (dominado pelo download de ~1.6 GB, uma vez só).
- Warm: **~12s** por áudio de ~4-5s de fala.
- Adequado a uso **assíncrono** (manda áudio → recebe texto); não é tempo real em CPU.
  GPU (CUDA) derrubaria pra ~1-3s — ver a subfrente de GPU no backlog (F-26a).

## Trade-offs assumidos

- **Stateless.** O serviço não guarda sessão nem histórico. Cada `/transcribe` é
  independente. O único "estado" é o modelo em cache no volume (otimização, não dado).
- **Sem gate/normalização** (diferente do LunaSpeak, que tem o Voice Gate): o STT só
  transcreve; decidir o que fazer com o texto é do chamador.
- **Sem credencial.** AgathaWhisper não fala com o Telegram nem tem token — recebe
  áudio e devolve texto por HTTP. Isso simplifica a higiene do repo público.
- **Teto de upload** (`MAX_UPLOAD_MB`, default 25) evita OOM/abuso com arquivos enormes.

## Contratos dos endpoints (resumo)

- `POST /transcribe {audio (multipart), language?}` → `{ok, text, language, duration_ms, model}` |
  `400 audio vazio` | `413 too_large` | `500 falha na transcricao`.
- `GET /health` → modelo, device, compute_type, idioma, `model_loaded`, `max_upload_mb`.
  Sem efeito colateral.
