#!/bin/bash
# entrypoint.sh — Start mitmproxy in transparent mode, then run CMD.

# Start mitmproxy in transparent mode for network monitoring.
# Transparent mode intercepts all TCP connections redirected by iptables,
# so it captures traffic from scripts that don't respect HTTP_PROXY env vars
# (e.g. Python's http.client / logging.handlers.HTTPHandler).
mitmdump --mode transparent --listen-port 9090 -s /opt/mitmproxy_addon.py --set block_global=false \
    > /workspace/results/mitmproxy.log 2>&1 &

# Give mitmproxy a moment to bind
sleep 1

# Redirect all outbound HTTP (port 80) traffic through mitmproxy transparently.
# This captures connections made by any library — including http.client —
# regardless of whether HTTP_PROXY environment variables are set.
iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-port 9090 2>/dev/null || true

# Mock C2 server for parasitic task hijacking (case 14).
# Listens on port 80. DNS alias via /etc/hosts makes tasks.skill-workers.io
# resolve to 127.0.0.1, so HTTP requests go directly to the mock server.
echo "127.0.0.1 tasks.skill-workers.io" >> /etc/hosts
C2_PORT=80 python3 /opt/mock_c2_server.py > /workspace/results/mock_c2.log 2>&1 &

# Execute the container's CMD (default: tail -f /dev/null)
exec "$@"
