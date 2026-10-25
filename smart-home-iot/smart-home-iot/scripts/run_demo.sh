#!/usr/bin/env bash
# Runs automation + dashboard + virtual devices in one terminal (no hardware needed).
# Requires a running broker and a configured .env.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
trap 'kill 0' EXIT
$PY -m smarthome.automation &
$PY -m smarthome.simulator &
$PY -m smarthome.dashboard.app &
echo "Dashboard: http://localhost:${DASH_PORT:-5000}   (Ctrl+C to stop)"
wait
