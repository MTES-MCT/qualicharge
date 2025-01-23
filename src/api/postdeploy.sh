#!/usr/bin/env bash

set -euo pipefail

echo "🗃️ Running database migrations..."
alembic -c qualicharge/alembic.ini upgrade head
