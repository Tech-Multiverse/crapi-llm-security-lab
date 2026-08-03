# crAPI-LLM Security Lab

> 🎬 Project article and video walkthrough(s) coming soon — stay tuned!

A local, shareable lab for API security, LLM application security, and agentic AI demos.

It combines the OWASP crAPI vulnerable API application with an Ollama LLM (local or remote), a LangGraph-based chatbot/MCP server, a custom Python agent, and an optional API gateway with traffic analysis.

## What this is for

This lab is a local, shareable environment for learning and practicing API security, LLM application security, and agentic AI security. It is meant to be:

- **Reproducible**: one `docker compose up` gets crAPI, the agent, the gateway, and the demo UI running.
- **Extensible**: built to add WAAP engines, centralized logging, LLM guardrails, and more advanced agent workflows.
- **Pedagogical**: directly maps to the OWASP API Security Top 10, OWASP LLM / AI security risks, WAAP and runtime security concepts, and agent-to-API/tool interactions.

## What crAPI (develop branch) gives us

The `develop` branch of OWASP crAPI includes:

- The classic OWASP API Security Top 10 challenges (BOLA, BFLA, broken auth, excessive data exposure, mass assignment, rate limiting, SSRF, NoSQL/SQL injection, JWT forgery, unauthenticated access).
- A built-in LLM chatbot (`crapi-chatbot`) that uses LangGraph to call crAPI APIs via an OpenAPI spec.
- An MCP (Model Context Protocol) server on port `5500` that exposes the same API surface as tools.
- LLM-specific challenges 16–18: prompt injection, credential extraction, and action-on-behalf-of-another-user.
- A fake external gateway service (`api.mypremiumdealership.com`) for the SSRF challenge.

## What we have added

- A top-level `docker-compose.yml` that `include`s crAPI's compose and exposes the direct service ports for local testing.
- A root `.env` with all the configuration in one place; copy it from `.env.example` and point it at your Ollama instance.
- A `crapi-llm` Miniconda environment for Python agent development.
- A small patch (`infrastructure/crapi-chatbot-patches/retriever_utils.py`) that makes crAPI's chatbot use `OllamaEmbeddings` for the vector store instead of `OpenAIEmbeddings`, which sends token arrays that Ollama's OpenAI-compatible `/v1/embeddings` endpoint rejects.
- A standalone `agent/` directory with command-line Python demos that drive crAPI through their own Ollama connection. These agents are not the same as crAPI's built-in chatbot service (`crapi-chatbot`); they call crAPI's REST APIs directly to demonstrate agentic API discovery, tool calling, and LLM-driven attacks.
- A `gateway/` directory with a Kong gateway, rate limiting, a WAF-style path block, Prometheus metrics, and a Grafana dashboard.
- A `ui/` directory with a Vite + React demo interface, plus `scripts/` with one-click attack/defense scenario scripts.

## Architecture

```
Host workstation
  ├─ Docker Desktop
  │   └─ crAPI stack
  │       ├─ crapi-identity      :8080
  │       ├─ crapi-community     :8087
  │       ├─ crapi-workshop      :8000
  │       ├─ crapi-chatbot       :5002 (chat) / :5500 (MCP)
  │       ├─ crapi-web           :8888
  │       ├─ postgres            :5432
  │       ├─ mongodb             :27017
  │       ├─ chromadb            :8000
  │       ├─ mailhog             :8025
  │       └─ api.mypremiumdealership.com
  │
  ├─ Conda env `crapi-llm`
  ├─ agent/ Python demos
  ├─ gateway/ Kong + Prometheus + Grafana
  └─ ui/ Vite + React demo interface

Ollama (local install, remote GPU box, or Docker)
  ├─ llama3.1:8b        (chat / tool calling)
  └─ nomic-embed-text:latest (embeddings)
```

## Network layout

`docker-compose.yml` uses the `include` directive to pull in `crapi/deploy/docker/docker-compose.yml` and then override selected ports.

- Docker Compose creates a default bridge network named `crapi-llm_default`.
- Inside that network, services talk to each other by container name (e.g. `crapi-chatbot` calls `http://crapi-identity:8080`).
- The host machine reaches published services on `127.0.0.1`:
  - `http://127.0.0.1:8888`   crAPI web UI
  - `http://127.0.0.1:8080`   identity service
  - `http://127.0.0.1:8087`   community service
  - `http://127.0.0.1:8000`   workshop service
  - `http://127.0.0.1:5002`   chatbot API (`/chatbot/genai/ask`)
  - `http://127.0.0.1:5500`   MCP server
  - `http://127.0.0.1:8025`   MailHog UI
  - `http://127.0.0.1:3001`   React demo UI (`crapi-ui`)
  - `http://127.0.0.1:8088`   Kong gateway proxy
  - `http://127.0.0.1:13000`  Grafana (admin/admin)
  - `http://127.0.0.1:19090`  Prometheus
- The `crapi-chatbot` container exits the Docker network to reach Ollama wherever it is running (local host, another container, or a remote GPU machine).

## Requirements

- macOS, Linux, or Windows with WSL2 / Docker Desktop (tested on macOS Intel / `x86_64`)
- Docker running
- Docker Compose v2.20+ (the root `docker-compose.yml` uses `include`)
- Miniconda (optional, for local Python agent dev)
- Node.js / `nvm` (optional, for React UI dev)
- Ollama reachable from Docker. Options:
  - **Local install** on the same machine running Docker (works with CPU or GPU)
  - **Remote machine** (e.g. Linux box with a GPU) on the same network
  - **Docker with GPU support** (optional, requires `nvidia-container-toolkit`)

## Quick start

1. Clone this repo:

   ```bash
   git clone <your-repo-url> crAPI-LLM
   cd crAPI-LLM
   ```

2. Clone the crAPI submodule:

   ```bash
   git clone --depth 1 --branch develop https://github.com/OWASP/crAPI.git crapi
   ```

3. Copy `.env` and point crAPI at your Ollama server:

   ```bash
   cp .env.example .env
   # edit .env and set OLLAMA_HOST_IP to the IP or hostname where Ollama is reachable
   # from the crAPI container (see "Pointing crAPI to Ollama" below for examples).
   ```

4. Make sure Docker Desktop is running, then start the stack (this also starts the gateway, Grafana, and React UI):

   ```bash
   docker compose up -d
   ```

5. Verify:

   ```bash
   docker compose ps
   curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8888
   ```

6. Open the demo UI at `http://127.0.0.1:3001`.

7. Test the chatbot from the command line:

   ```bash
   curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
     -H "Content-Type: application/json" \
     -d '{"message":"hello"}'
   ```

## Pointing crAPI to Ollama

The chatbot and agent use the OpenAI-compatible endpoint that Ollama exposes on port `11434`. Update `.env` so the crAPI container can reach it.

Common setups:

| Where Ollama runs | `OLLAMA_HOST_IP` value | Notes |
|---------------------|-------------------------|-------|
| Same host as Docker Desktop (macOS/Windows) | `host.docker.internal` | Docker Desktop resolves this to the host. |
| Same host, Linux Docker Engine | LAN IP of the host (e.g. `192.168.1.42`) or `172.17.0.1` | `host.docker.internal` is not automatic on Linux Docker Engine. |
| Remote GPU box / another machine | Its IP (e.g. `192.168.1.50`) | Firewall must allow TCP `11434` from the Docker host. |

For example, with a remote GPU machine:

```bash
OLLAMA_HOST_IP=192.168.1.50
CHATBOT_OPENAI_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1/
```

For a local Ollama on Docker Desktop macOS/Windows:

```bash
OLLAMA_HOST_IP=host.docker.internal
CHATBOT_OPENAI_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1/
```

For the agent running on the host (not in Docker), you can also export:

```bash
export OLLAMA_BASE_URL=http://${OLLAMA_HOST_IP}:11434/v1
```

After editing `.env`, recreate the chatbot container:

```bash
docker compose up -d
```

## Ollama setup

These instructions work on Linux, macOS, or Windows (with WSL2 / Docker). They assume you want to keep everything self-hosted; no third-party LLM API account is needed.

### 1. Install Ollama

Follow the official guide for your OS:

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: use the installer from https://ollama.com/download/windows
# or run inside WSL2 with the same command as Linux.
```

### 2. Pull the models

Recommended models that fit on an 8 GB GPU or a CPU host:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
```

### 3. Expose Ollama to the network

By default Ollama only listens on `127.0.0.1:11434`. If you run crAPI in Docker, the container needs to reach it, so bind to all interfaces:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

On Windows Command Prompt:

```cmd
set OLLAMA_HOST=0.0.0.0
ollama serve
```

On Windows PowerShell:

```powershell
$env:OLLAMA_HOST="0.0.0.0"
ollama serve
```

If Ollama is on a remote machine, make sure the host firewall allows inbound TCP `11434` from the Docker host's subnet.

### 4. Optional: store models on a different drive

On Windows:

```cmd
set OLLAMA_MODELS=D:\OllamaModels
```

On Linux / WSL2:

```bash
export OLLAMA_MODELS=/mnt/d/OllamaModels
```

## Tested configuration

This repo was developed with:

- A Mac host running Docker Desktop
- A separate Linux machine with an NVIDIA GPU running Ollama (`llama3.1:8b` and `nomic-embed-text:latest`)
- The Mac reaching Ollama over the LAN at `http://192.168.4.55:11434/v1`

Any setup where Docker can reach Ollama at the URL you put in `.env` should work the same way.

## Why the `retriever_utils.py` patch?

crAPI's chatbot is hard-coded to use `OpenAIEmbeddings` for the `openai` provider. `OpenAIEmbeddings` tokenizes text with `tiktoken` and sends token-id arrays to `/v1/embeddings`. Ollama's OpenAI-compatible endpoint expects strings, so it returns `invalid input type`.

The patch in `infrastructure/crapi-chatbot-patches/retriever_utils.py` swaps in `OllamaEmbeddings` whenever a non-default `CHATBOT_OPENAI_BASE_URL` is set, and it is mounted over `/app/chatbot/retriever_utils.py` in the `crapi-chatbot` container.

## React demo UI and scenario scripts

A Vite + React UI is bundled as the `crapi-ui` container and served on port `3001`:

- **Chatbot** tab — talk to the crAPI chatbot through Ollama.
- **API Explorer** tab — send requests directly to crAPI endpoints.
- **Scenarios** tab — replay attack/defense demos with one click (rate-limit DoS, SSRF block, prompt injection, NoSQL coupon injection).

Open `http://127.0.0.1:3001` after `docker compose up -d`.

Command-line equivalents live in `scripts/`:

```bash
./scripts/rate-limit-demo.sh
./scripts/ssrf-blocked-demo.sh
./scripts/prompt-injection-demo.sh
./scripts/agent-demo.sh
```

## Roadmap and future additions

For the full phased plan, see `ROADMAP.md`.

crAPI gives us the vulnerable API and a built-in LLM chatbot. This repo extends it with an Ollama-backed agent, a Kong gateway with metrics, and a React demo UI. Possible next additions:

1. **WAAP / ModSecurity / open-appsec**  
   Replace or augment the simple Kong path block with a real WAAP engine and OWASP CRS rules.

2. **Centralized log analysis**  
   Add Loki, Vector, or ClickHouse to collect request/response bodies and agent logs for forensic replay.

3. **LLM guardrails**  
   Experiment with input/output filtering, prompt-injection detection, and tool-call confirmation UIs.

4. **Advanced agentic demos**  
   Multi-step agent attacks, autonomous discovery, and agent-to-agent workflows.

5. **Write-ups refresh**  
   Keep mapping new challenges and mitigations to OWASP API Security, OWASP LLM / AI security risks, and NIST AI RMF.

## Project layout

```
crAPI-LLM/
├── .env                           # Docker Compose environment
├── docker-compose.yml             # includes crAPI + port overrides + patch mount
├── README.md                      # this file
├── agent/                         # custom Python agent demos
├── docs/                          # write-ups and challenge mapping
├── gateway/                       # Kong + Prometheus + Grafana configs
├── scripts/                       # one-click attack/defense scenario scripts
├── infrastructure/               # support files for the lab
│   └── crapi-chatbot-patches/
│       └── retriever_utils.py    # Ollama embedding fix
├── ui/                           # Vite + React demo interface
└── crapi/                        # cloned OWASP crAPI (develop branch)
```

## Useful commands

```bash
# View all running crAPI services
docker compose ps

# Follow the chatbot logs
docker compose logs -f crapi-chatbot

# Stop everything
docker compose down

# Stop and remove data volumes (destructive)
docker compose down -v

# Test the chatbot directly
curl -s -X POST http://127.0.0.1:5002/chatbot/genai/ask \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'

# Test Ollama from the Docker host
curl http://${OLLAMA_HOST_IP}:11434/api/tags
```

## License

This project structure and documentation are provided for educational and demo purposes. crAPI itself is licensed under Apache 2.0.
