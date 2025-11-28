#!/usr/bin/env bash

set -eo pipefail

echo "🚀 Will start prefect server…"

# Get details about prefect installation
prefect version

# Run prefect server
prefect server start --host 0.0.0.0 --port "${PORT}" --workers 1
