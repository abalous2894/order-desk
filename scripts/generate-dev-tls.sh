#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -subj "/CN=localhost/O=Order Desk Dev/C=US" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "Wrote $CERT_DIR/cert.pem and $CERT_DIR/key.pem"
echo "Start with TLS: docker compose -f docker-compose.yml -f docker-compose.tls.yml up --build"
