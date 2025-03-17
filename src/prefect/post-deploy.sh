#!/usr/bin/env bash

set -eo pipefail

declare YQ_VERSION="v4.44.6"
declare YQ_BINARY="yq_linux_amd64"
declare YQ="/tmp/${YQ_BINARY}"

# Run database migrations
echo "🗃️ Will run database migrations…"
prefect server database upgrade -y

# Create worker pool
echo "👷 Will create 'indicators' worker pool…"
prefect work-pool create --type process --overwrite indicators
