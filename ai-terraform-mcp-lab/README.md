# AI Terraform MCP Lab

Small lab combining Ollama, Model Context Protocol (MCP), Terraform modules and GitHub.

## Goal

Type:

> Quiero crear un Storage Account

The agent asks for missing values, reads the approved module through MCP, generates Terraform, validates it, creates a feature branch, commits the code and opens a draft Pull Request.

The lab intentionally stops before `terraform apply`.

## Quick start

1. Copy `.env.example` to `.env` and set `GITHUB_TOKEN`.
2. Start Ollama and download the model:
```bash
docker compose up -d ollama
docker compose exec ollama ollama pull qwen3:8b
```
3. Create the Python environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
4. Run:
```bash
./scripts/run-agent.sh
```

The agent should ask for environment, name, resource group, location and replication.

## Safety boundary

No `terraform apply`. The AI never writes directly to `master`.

For a production platform, add policy checks, secret scanning, Checkov/TFLint, OPA/Conftest, Azure authentication and CI plan approval before merge.
