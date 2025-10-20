#!/usr/bin/env bash

# Test execution wrapper script
# Extracted from the original run script

set -o errexit
set -o pipefail

# Source docker helper functions
# shellcheck source=scripts/docker-helper.sh
source "$(dirname "$0")/docker-helper.sh"

main() {
  echo "🧪 Running full Django test suite..."
  echo ""

  # We need to collectstatic before we run our tests.
  _dc web python3 manage.py collectstatic --no-input

  # Run all tests (without parallel flag to ensure sequential execution)
  _dc -e DJANGO_TESTING=true -e RUNNING_TESTS=true web python3 manage.py test
  local exit_code=$?

  if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests passed successfully!"
  else
    echo ""
    echo "❌ Some tests failed. Exit code: $exit_code"
  fi

  return $exit_code
}

main "$@"
