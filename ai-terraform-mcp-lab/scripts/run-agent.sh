#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT:$PYTHONPATH"

if [[ ! -f .env ]]; then
  echo "Create ai-terraform-mcp-lab/.env from .env.example first."
  exit 1
fi

set -a
source .env
set +a

python -m ai_terraform_mcp_lab.agent.main
