#!/usr/bin/env bash
set -euo pipefail

# Remove the jump from DOCKER-USER
iptables -D DOCKER-USER -j HW4-AGENT 2>/dev/null || true

# Remove rules inside the HW4-AGENT chain
iptables -F HW4-AGENT 2>/dev/null || true

# Delete the now-empty HW4-AGENT chain
iptables -X HW4-AGENT 2>/dev/null || true
