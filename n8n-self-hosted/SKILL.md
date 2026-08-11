---
name: n8n-self-hosted
description: Expert guidance for running a self-hosted n8n instance with local AI using the official Docker Compose starter kit (github.com/n8n-io/self-hosted-ai-starter-kit). Auto-load when the user asks about self-hosting n8n, local AI, Ollama, Qdrant, setting up Docker Compose for n8n, or the self-hosted AI starter kit. Sourced from the self-hosted-ai-starter-kit README (fetched 2026-05-15).
---

# n8n Self-Hosted AI Starter Kit

> Adapted from the n8n self-hosted-ai-starter-kit README (`github.com/n8n-io/self-hosted-ai-starter-kit`, fetched 2026-05-15), © 2024–present n8n GmbH, Apache License 2.0.

The starter kit is a Docker Compose template that bundles:
- **n8n** — self-hosted workflow automation (400+ integrations, AI nodes)
- **Ollama** — local LLM platform (run Llama, Mistral, etc. on-device)
- **Qdrant** — open-source vector store for RAG workflows
- **PostgreSQL** — persistent storage for n8n and vector data

## Installation

```bash
git clone https://github.com/n8n-io/self-hosted-ai-starter-kit.git
cd self-hosted-ai-starter-kit
cp .env.example .env   # update secrets and passwords inside
```

Never commit `.env`. Generate a strong `N8N_ENCRYPTION_KEY` and back it up separately — losing it orphans every stored credential. Complete the owner-account setup immediately after first start, and never expose port 5678 beyond localhost without TLS + authentication (reverse proxy) — an unclaimed setup wizard on a public interface is an instance takeover.

## Running (by GPU type)

```bash
# Nvidia GPU
docker compose --profile gpu-nvidia up

# AMD GPU (Linux only)
docker compose --profile gpu-amd up

# CPU only / Mac without GPU acceleration
docker compose --profile cpu up

# Mac with Ollama running natively (faster inference)
docker compose up
```

**For Mac users with native Ollama:**
1. Set `OLLAMA_HOST=host.docker.internal:11434` in `.env`
2. After startup, go to `http://localhost:5678/home/credentials` → "Local Ollama service" → change base URL to `http://host.docker.internal:11434/`

## Accessing n8n

Open `http://localhost:5678/` after startup. First run triggers a one-time setup wizard.

The bundled starter workflow is at: `http://localhost:5678/workflow/srOnR8PAY3u4RSwb`

## Upgrading

```bash
# Nvidia
docker compose --profile gpu-nvidia pull
docker compose create && docker compose --profile gpu-nvidia up

# CPU only
docker compose --profile cpu pull
docker compose create && docker compose --profile cpu up

# Mac with native Ollama (no profile)
docker compose pull
docker compose create && docker compose up
```

For production/company environments: pin image tags (or digests) in the compose file, review the n8n changelog before upgrading, and back up the Postgres volume and `N8N_ENCRYPTION_KEY` before pulling new images.

## Accessing local files from nodes

The shared folder (mounted at `/data/shared` inside the n8n container) lets workflows access local files. Nodes that work with it:
- Read/Write Files from Disk
- Local File Trigger
- Execute Command

## Key AI nodes available

Once running, n8n includes:
- **AI Agent** — LangChain-based multi-tool orchestration
- **Text Classifier** — route on natural language input
- **Information Extractor** — pull structured fields from text
- **Ollama** — local LLM node (use for fully local, no-API-key workflows)
- **Qdrant** — vector store node for RAG

For local-only workflows: use **Ollama node** (not OpenAI) + **Qdrant** as the vector store.

## What you can build locally

- AI agents that schedule appointments
- Summarize PDFs securely (no data leaves your machine)
- Smarter Slack bots
- Private financial document analysis
- Any RAG workflow with Qdrant + Ollama

## Useful AI templates (importable into self-hosted instance)

| Template | What it does |
|---|---|
| AI Agent Chat | Basic conversational AI agent |
| AI chat with any data source | Connect LLM to any data |
| Chat with PDF docs using AI | RAG over PDFs with source citations |
| AI agent that can scrape webpages | Web scraping + LLM — scraped page text is attacker-controlled input to the agent; don't pair an open-ended scraping tool with write-capable tools, and allowlist domains |
| Tax Code Assistant | Qdrant + Mistral RAG over tax docs |
| Recipe Recommendations with Qdrant and Mistral | Vector search + LLM |

Import: open n8n UI → New Workflow → "Use workflow" button from `n8n.io/workflows/categories/ai/`.

## Cloud vs self-hosted differences

| Feature | Cloud (`<your-instance>.app.n8n.cloud`) | Self-hosted |
|---|---|---|
| Credentials | n8n credential store | n8n credential store |
| API | `https://<your-instance>.app.n8n.cloud/api/v1` | `http://localhost:5678/api/v1` |
| Ollama | Use a hosted LLM (e.g. `openai/gpt-4o-mini`); if using OpenRouter, pin an explicitly verified-live model id — retired model ids 404 at runtime, often only on rarely-exercised paths, and a missing `model` field silently runs the node default | Use local Ollama node |
| Vector store | Hosted vector store (e.g. Supabase, Pinecone) | Qdrant (local) |
| File access | Limited | `/data/shared` volume |
| Updates | Automatic | Manual (`docker compose pull`) |

## Attribution

Adapted from the n8n self-hosted-ai-starter-kit README (github.com/n8n-io/self-hosted-ai-starter-kit), © 2024–present n8n GmbH, Apache License 2.0; condensed and modified 2026-08-11. See `n8n-pack/LICENSE` and `n8n-pack/NOTICE`.
