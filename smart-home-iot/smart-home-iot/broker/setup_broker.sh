#!/usr/bin/env bash
# Installs Mosquitto on Raspberry Pi OS / Debian / Ubuntu and creates the users.
# Usage: sudo ./broker/setup_broker.sh <admin_password> <node_password>
set -euo pipefail

ADMIN_PASS=${1:?usage: sudo $0 <admin_password> <node_password>}
NODE_PASS=${2:?usage: sudo $0 <admin_password> <node_password>}
HERE="$(cd "$(dirname "$0")" && pwd)"

apt-get update
apt-get install -y mosquitto mosquitto-clients

mosquitto_passwd -b -c /etc/mosquitto/passwd admin "$ADMIN_PASS"
mosquitto_passwd -b /etc/mosquitto/passwd node "$NODE_PASS"
install -m 640 -o mosquitto -g mosquitto "$HERE/acl" /etc/mosquitto/acl
install -m 644 "$HERE/smarthome.conf" /etc/mosquitto/conf.d/smarthome.conf
chown mosquitto:mosquitto /etc/mosquitto/passwd
chmod 640 /etc/mosquitto/passwd

systemctl enable mosquitto
systemctl restart mosquitto
echo "Broker ready on port 1883. Test with:"
echo "  mosquitto_sub -h localhost -u admin -P '<admin_password>' -t 'home/#' -v"
