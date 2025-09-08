set -euo pipefail

mkdir -p /app/data/exports /app/data/imports

exec "$@"
