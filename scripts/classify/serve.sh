#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0
# Reinit oxigraph, load graph, serve oxigraph + trifid.
# Both processes are killed on exit (Ctrl-C or signal).
set -euo pipefail

OXI_DIR=~/oxi
TTL="${GRAPH}/estate.ttl"

cleanup() {
    echo "Shutting down..."
    kill $OXI_PID $TRIFID_PID 2>/dev/null
    wait $OXI_PID $TRIFID_PID 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# Reinit and load
rm -rf "$OXI_DIR"
oxigraph load -f "$TTL" -l "$OXI_DIR"
oxigraph optimize -l "$OXI_DIR"

# Serve
oxigraph serve -l "$OXI_DIR" --cors &
OXI_PID=$!

# Wait for oxigraph to be ready
for i in $(seq 1 30); do
    curl -s http://localhost:7878/query -H "Content-Type: application/sparql-query" -d "ASK { ?s ?p ?o }" >/dev/null 2>&1 && break
    sleep 0.5
done

npx trifid --sparql-endpoint-url=http://localhost:7878/query &
TRIFID_PID=$!

echo "Oxigraph PID=$OXI_PID, Trifid PID=$TRIFID_PID"
echo "Ctrl-C to stop both."
wait
