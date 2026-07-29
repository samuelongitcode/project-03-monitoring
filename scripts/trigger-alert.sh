#!/bin/bash
# Hits /api/fail repeatedly to actually trigger the HighErrorRate alert
# rule — this is the "break it on purpose" step. Don't skip it.
#
# Usage: ./scripts/trigger-alert.sh [duration_seconds]
DURATION="${1:-60}"
END=$((SECONDS + DURATION))
COUNT=0

echo "Hammering http://localhost:8000/api/fail for ${DURATION}s..."
echo "Watch Prometheus (http://localhost:9090/alerts) or Alertmanager"
echo "(http://localhost:9093) — the HighErrorRate alert should go from"
echo "'inactive' to 'pending' to 'firing' within about 30-40 seconds."
echo ""

while [ $SECONDS -lt $END ]; do
    curl -s http://localhost:8000/api/fail > /dev/null
    COUNT=$((COUNT + 1))
    sleep 0.2
done

echo ""
echo "Sent ${COUNT} failing requests. Check the Prometheus/Alertmanager UIs now."
