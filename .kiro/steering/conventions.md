---
inclusion: auto
name: conventions
description: Use ao contribuir com o AgathaWhisper — padrão de config por env, higiene de repositório público, e estilo de código/issue/commit.
---

# Convenções — AgathaWhisper

## Config por env (sem rebuild)

Toda opção de runtime é uma **variável de ambiente** com default sensato, lida uma
vez no topo de `app/main.py`. Trocar comportamento (modelo, device, idioma) é editar
o `.env` e reiniciar o container — **nunca** rebuildar a imagem. Regras:

- Todo env novo entra no `.env.example` com comentário curto do que faz + default.
- Quando fizer sentido, exponha o valor efetivo no `GET /health` (ex. `model`, `device`,
  `language`) — facilita confirmar o que está no ar.
- Default = comportamento seguro/leve. Uma flag nova nunca muda o comportamento de quem
  não a setou.

Envs atuais: `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`,
`WHISPER_LANGUAGE`, `MAX_UPLOAD_MB`, `MODEL_DIR`, `LOG_LEVEL`. Tabela com defaults no
`README.md`.

## Higiene de repositório PÚBLICO

Este repo é **público**. Nunca versione dado local/pessoal/de infra:

- **Zero** IP de host, path de host, `chat_id`, token, nome de máquina ou de rede
  doméstica — em código, README, steering, issues ou mensagens de commit.
- Use **placeholders genéricos**: `<HOST>`, `<APP_DIR>`, porta genérica.
- O AgathaWhisper **não tem credencial** (não fala com o Telegram) — mas mesmo assim
  nada de infra pessoal no versionado.
- `.env`/`.env.deploy` e o cache de modelo (`.models/`) são gitignored.

## Estilo de código

- Python 3.12, FastAPI. I/O e rotas em `app/main.py`.
- Modelo carregado **lazy** (singleton em `_get_model()`), nunca no import.
- Logs **estruturados** por request (modelo, idioma detectado, duração, bytes), **sem**
  vazar o texto transcrito integral em nível INFO além do necessário.
- Toda feature de comportamento observável vem com teste de regressão quando houver
  suíte (pytest + TestClient; mockar o modelo pra não baixar peso no CI).

## Estilo de issue / commits

- Issue **antes** do PR (issue-first): Contexto/Problema → Proposta → Critérios de
  aceite (checklist) → Notas técnicas. PR referencia com `Closes #N`.
- Commit no imperativo, escopo no título (`feat:`, `docs:`, `fix:` …), corpo explica o
  **porquê** e o que ficou fora de escopo.
