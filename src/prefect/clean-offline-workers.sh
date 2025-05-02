#!/usr/bin/env bash

set -eo pipefail

declare work_pool="indicators"
declare workers

# Get offline workers
workers=$(curl -s \
  -X POST \
  "${PREFECT_API_URL}work_pools/${work_pool}/workers/filter" \
  --header "Content-Type: application/json"  \
  --data '{"workers": {"status": {"any_": ["OFFLINE"]}}}' |\
  jq -r .[].name |\
  sed "s/ /%20/g")

# Delete offline workers
for worker in ${workers}; do
  echo "Deleting worker ${worker}…"
  curl -s \
    -X DELETE \
    "${PREFECT_API_URL}work_pools/${work_pool}/workers/${worker}"
done
