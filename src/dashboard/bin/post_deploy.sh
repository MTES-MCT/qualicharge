#!/usr/bin/env bash

set -euo pipefail


echo "🗃️ Apply new migrations"
python3 manage.py migrate --noinput
