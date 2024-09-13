#!/usr/bin/env bash

set -eo pipefail

# Create worker pool
prefect work-pool create --type process --overwrite indicators

# Create or update deployments
prefect deploy
