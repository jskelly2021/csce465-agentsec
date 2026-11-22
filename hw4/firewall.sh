#!/usr/bin/env bash
set -euo pipefail

modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-iptables=1

# 1. Create custom chain if it doesn't exist
iptables -N HW4-AGENT 2>/dev/null || true
iptables -F HW4-AGENT

# 2. Connect the HW4-AGENT chain to DOCKER-USER
iptables -C DOCKER-USER -j HW4-AGENT 2>/dev/null ||
  iptables -I DOCKER-USER 1 -j HW4-AGENT

# 3. Allow established and related traffic
iptables -A HW4-AGENT \
  -m conntrack --ctstate ESTABLISHED,RELATED \
  -j RETURN

# 4. Allow new connections to web-lab TCP 8000
iptables -A HW4-AGENT \
  -s 172.30.0.10 \
  -d 172.30.0.40 \
  -p tcp --dport 8000 \
  -m conntrack --ctstate NEW \
  -j RETURN

# 5. Log new connections to mock-c2 TCP 8080
iptables -A HW4-AGENT \
  -s 172.30.0.10 \
  -d 172.30.0.66 \
  -p tcp --dport 8080 \
  -m conntrack --ctstate NEW \
  -j LOG --log-prefix "HW4-C2-DROP: "

# 6. Drop those C2 connection attempts
iptables -A HW4-AGENT \
  -s 172.30.0.10 \
  -d 172.30.0.66 \
  -p tcp --dport 8080 \
  -m conntrack --ctstate NEW \
  -j DROP

# 7. Drop all other new agent connections
iptables -A HW4-AGENT \
  -s 172.30.0.10 \
  -m conntrack --ctstate NEW \
  -j DROP

# 8. Return all remaining traffic to Docker
iptables -A HW4-AGENT -j RETURN
