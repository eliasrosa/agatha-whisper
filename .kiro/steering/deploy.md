---
inclusion: auto
name: deploy
description: Use quando o usuário perguntar sobre deploy, CI/CD, ZimaOS ou pipeline de entrega do AgathaWhisper.
---

# Deploy — ZimaOS

Mesmo padrão do LunaSpeak / wallet-app: **imagem local (sem registry)**, deploy no host
do homelab. O compose de produção é o `docker-compose-zimaos.yml` (porta **8094**), copiado
para `APP_DIR` (sob `…/casaos/apps/agathawhisper`) com o `.env` de prod ao lado — subir por
aí é o que registra o **card** no CasaOS.

## Deploy (via SSH root no ZimaOS)

1. Enviar o build context pro ZimaOS (tar-over-ssh; rsync pode não existir no ambiente do agente).
2. Copiar `docker-compose-zimaos.yml` → `${APP_DIR}/docker-compose.yml` e gerar o `.env` de prod
   (só config de modelo — o AgathaWhisper **não tem segredo**).
3. `docker build -t agathawhisper:latest .` no próprio ZimaOS.
4. `docker compose -f docker-compose.yml up -d --force-recreate`.

> Validado 11/09: container `agathawhisper` no ar na 8094, `/health` verde, `/transcribe` e2e OK.

## Config por env (prod)

`WHISPER_MODEL` (prod atual: `large-v3-turbo`), `WHISPER_DEVICE=cpu`,
`WHISPER_COMPUTE_TYPE=int8`, `WHISPER_LANGUAGE=pt`, `MAX_UPLOAD_MB=25`, `LOG_LEVEL=INFO`.
Trocar o modelo = editar o `.env` + `docker compose up -d --force-recreate` (sem rebuild).

## Arquivos

| Arquivo | Papel |
|---------|-------|
| `Dockerfile` | Imagem (python-slim + ffmpeg + faster-whisper) |
| `docker-compose-zimaos.yml` | Compose de produção (imagem local, `pull_policy: never`, `x-casaos`, porta 8094) |
| `docker-compose.yml` | Ambiente de **dev** (porta 8034) — não usado em prod |
| `.env.example` | Modelo das envs (o `.env` real é gitignored) |

## Infraestrutura ZimaOS

| Item | Valor |
|------|-------|
| IP | `<ZIMAOS_IP>` |
| Porta | `<HOST_PORT>` (8094 host) → `8080` (container) |
| App dir (CasaOS) | `<APP_DIR>` — convenção `…/casaos/apps/agathawhisper` (dá o card) |
| Volume do modelo | `agathawhisper_models` (cache do whisper, persiste entre restarts) |

## GPU (futuro — ver subfrente F-26a no vault)

O ZimaOS tem NVIDIA MX330 (2 GB) com o NVIDIA Container Toolkit já instalado (runtime
`nvidia` no Docker). Migrar pra GPU (~12s → ~1-3s) exige rebuild com libs CUDA/cuDNN +
compose com `runtime: nvidia` + `WHISPER_DEVICE=cuda`/`float16`. Cuidado: 2 GB de VRAM é
apertado pro `large-v3-turbo` — preferir modelo menor (`small`/`base`/`distil`).

## Regras

- Imagem local (`pull_policy: never`) — não publica em registry.
- Compose de produção = `docker-compose-zimaos.yml` (não o de dev).
- `APP_DIR` sob o dir de apps do CasaOS (convenção `…/casaos/apps/<app>`).
- Nunca `sudo` no workflow; operações privilegiadas via SSH.
- Dados de infra pessoal (IP/porta/paths) só via placeholders — o repo é **público**.
