#!/usr/bin/env bash
# Creates a private CA and a broker certificate for TLS experiments.
# Usage: ./tools/gen_certs.sh <pi-hostname-or-ip> [output-dir]
set -euo pipefail

HOST=${1:?usage: $0 <pi-hostname-or-ip> [output-dir]}
OUT=${2:-certs}
mkdir -p "$OUT" && cd "$OUT"

if [[ $HOST =~ ^[0-9.]+$ ]]; then SAN="IP:$HOST"; else SAN="DNS:$HOST"; fi

openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 825 \
  -subj "/CN=SmartHome-CA" -out ca.crt
openssl genrsa -out server.key 2048
openssl req -new -key server.key -subj "/CN=$HOST" -out server.csr
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 825 -sha256 -extfile <(printf "subjectAltName=%s\n" "$SAN")
rm -f server.csr ca.srl

echo "Created ca.crt, server.crt, server.key in $(pwd)"
echo "Next: sudo mkdir -p /etc/mosquitto/certs && sudo cp ca.crt server.crt server.key /etc/mosquitto/certs/"
echo "      sudo chown mosquitto: /etc/mosquitto/certs/server.key && sudo chmod 600 /etc/mosquitto/certs/server.key"
echo "Then uncomment the 8883 listener in /etc/mosquitto/conf.d/smarthome.conf and restart mosquitto."
