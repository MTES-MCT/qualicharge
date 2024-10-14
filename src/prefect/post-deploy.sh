#!/usr/bin/env bash

set -eo pipefail

# Run database migrations
prefect server database upgrade -y

# Create worker pool
prefect work-pool create --type process --overwrite indicators

# Create or update deployments
prefect deploy
