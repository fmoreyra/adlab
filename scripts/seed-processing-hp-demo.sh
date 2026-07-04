#!/usr/bin/env bash

# Create histopathology protocol(s) ready for manual processing QA (Punto 2).
# Usage:
#   ./scripts/seed-processing-hp-demo.sh
#   ./scripts/seed-processing-hp-demo.sh --scenario all
#   ./scripts/seed-processing-hp-demo.sh --scenario stages

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/docker-helper.sh
source "$SCRIPT_DIR/docker-helper.sh"

main() {
  if ! command -v docker compose &>/dev/null; then
    echo "docker compose is not installed or not in PATH" >&2
    exit 1
  fi

  if ! docker compose ps web 2>/dev/null | grep -q "Up"; then
    echo "Web service is not running. Start with: docker compose up -d" >&2
    exit 1
  fi

  _dc web python3 manage.py seed_processing_hp_demo "$@"
}

main "$@"
