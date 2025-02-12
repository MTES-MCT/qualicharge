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

# Download yq
echo "🌍 Will download and install YQ…"
curl -sL "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${YQ_BINARY}.tar.gz" | \
  tar xz -C /tmp

# Create or update deployments
echo "⚙️  Will create or update deployments…"
for deployment in $(${YQ} .deployments.[].name < prefect.yaml); do
  echo "🚀 deployment ${deployment}"
  prefect deploy -n "${deployment}"
done
