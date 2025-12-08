#!/usr/bin/env bash

set -eo pipefail

echo "🚀 Will start prefect server…"

# Get details about prefect installation
prefect version

# Run prefect server
python3 -m uvicorn \
  --factory prefect.server.api.server:create_app \
  --host $PREFECT_SERVER_API_HOST \
  --port $PREFECT_SERVER_API_PORT \
  --log-level info
