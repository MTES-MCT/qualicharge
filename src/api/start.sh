#!/usr/bin/env bash

# We may expect that the following environment variables are set:
#
#   - PORT: the server port
#   - QUALICHARGE_DEBUG: activate the debug mode (for development) [*]
#
# [*] optional

set -eo pipefail

declare -i debug=${QUALICHARGE_DEBUG:-0}
declare -a extra_opts

if [ ${debug} == 1 ]; then
  extra_opts=(
    "--reload" \
    "--log-config logging-config.dev.yaml"
  )
  echo "⚗️ DEBUG mode activated. We hope your are not running in production. 🤞"
else
  extra_opts=(
    "--log-config logging-config.prod.yaml"
  )
fi

echo "🗃️ Running database migrations..."
alembic -c qualicharge/alembic.ini upgrade head

# shellcheck disable=SC2068
uvicorn \
  qualicharge.api:app \
  --proxy-headers \
  --host 0.0.0.0 \
  --port "${PORT}" \
  ${extra_opts[@]}
