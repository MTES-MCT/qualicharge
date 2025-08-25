#!/usr/bin/env bash

set -eo pipefail

# Run database migrations
echo "🗃️ Will run database migrations…"
prefect server database upgrade -y

# Create worker pool if the API is up and running
if [ "$(curl -s "${PREFECT_API_URL}health")" == "true" ]; then
  echo "👷 Will create 'indicators' worker pool…"
  prefect work-pool create --type process --overwrite indicators
else
  echo "❌ API looks down or unhealthy, will not create worker pool"
fi
