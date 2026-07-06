#!/usr/bin/env bash
#
# Run a bin/*.sh script inside a Linux container (docker:27-cli).
# Use on macOS so backup/restore scripts see the same GNU tooling as Ubuntu VPS.
#
# Usage:
#   ./bin/run-linux.sh backup-complete
#   ./bin/run-linux.sh restore-complete backups/adlab_complete_20260704_120000
#
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <script-basename> [args...]"
  echo ""
  echo "Examples:"
  echo "  $0 backup-complete"
  echo "  $0 restore-complete backups/adlab_complete_20260704_120000"
  exit 1
fi

SCRIPT_NAME="$1"
shift

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_FILE="${ROOT}/bin/${SCRIPT_NAME}.sh"

if [[ ! -f "$SCRIPT_FILE" ]]; then
  echo "Error: script not found: ${SCRIPT_FILE}"
  exit 1
fi

if [[ ! -f "${ROOT}/.env" ]]; then
  echo "Error: .env not found in ${ROOT}"
  exit 1
fi

# shellcheck disable=SC1091
set -a
source "${ROOT}/.env"
set +a

IMAGE="${OPS_RUNNER_IMAGE:-docker:27-cli}"

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

# Build quoted args for the inner shell (portable across bash versions).
inner_args=""
for arg in "$@"; do
  inner_args+=" $(printf '%q' "$arg")"
done

echo "Running bin/${SCRIPT_NAME}.sh inside ${IMAGE} (Linux environment)..."

docker run --rm \
  -v "${ROOT}:/workspace" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -w /workspace \
  -e COMPOSE_PROJECT_NAME \
  -e UID \
  -e GID \
  "${IMAGE}" \
  sh -c "
    set -e
    apk add --no-cache bash gzip coreutils findutils git >/dev/null 2>&1
    cd /workspace
    exec bash bin/${SCRIPT_NAME}.sh${inner_args}
  "
