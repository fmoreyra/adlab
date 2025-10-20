#!/usr/bin/env bash

# Docker Compose helper functions for Makefile
# Extracted from the original run script

set -o errexit
set -o pipefail

# Docker Compose command (default: exec)
DC="${DC:-exec}"

# If we're running in CI we need to disable TTY allocation for docker compose
# commands that enable it by default, such as exec and run.
TTY="${TTY:-}"
if [[ ! -t 1 ]]; then
  TTY="-T"
fi

_dc() {
  # shellcheck disable=SC2086
  docker compose "${DC}" ${TTY} "${@}"
}

_dc_run() {
  DC="run" _dc --no-deps --rm "${@}"
}

# Export functions so they can be used by other scripts
export -f _dc
export -f _dc_run
