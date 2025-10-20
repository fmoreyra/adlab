#!/usr/bin/env bash

# Django manage.py wrapper script
# Extracted from the original run script

set -o errexit
set -o pipefail

# Source docker helper functions
# shellcheck source=scripts/docker-helper.sh
source "$(dirname "$0")/docker-helper.sh"

main() {
  local command="${1:-}"

  # We need to collectstatic before we run our tests.
  if [ "${command}" == "test" ]; then
    _dc web python3 manage.py collectstatic --no-input
  fi

  # Set test environment variables for test commands
  if [ "${command}" == "test" ]; then
    _dc -e DJANGO_TESTING=true -e RUNNING_TESTS=true web python3 manage.py "${@}"
  else
    _dc web python3 manage.py "${@}"
  fi
}

main "$@"
