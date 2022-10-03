#!/bin/sh

set -eu

# Add system user zytempmqtt

SRVNAME="zytempmqtt"

ID=$(id -u ${SRVNAME} 2>/dev/null || true)

if [ -f /usr/sbin/nologin ]; then
    USERSHELL="/usr/sbin/nologin"
elif [ -f /sbin/nologin ]; then
    USERSHELL="/sbin/nologin"
else
    USERSHELL="/bin/false"
fi

if [ ! $(getent group ${SRVNAME}) ]; then
    groupadd -f ${SRVNAME}
    echo "group: added ${SRVNAME}"
fi

if [ -z "$ID" ]; then
    useradd --system --shell $USERSHELL -g ${SRVNAME} ${SRVNAME}
    echo "user: added ${SRVNAME}"
fi

# Install udev rule

if grep -qa container=lxc /proc/1/environ; then
    echo "Skipping udev rules in lxc"
else
    cp -a udev/90-usb-zytemp-permissions.rules /etc/udev/rules.d/
    udevadm control --reload-rules
    udevadm trigger
fi

# Create default config

mkdir -p /etc/zytempmqtt
cat <<'EOF' > /etc/zytempmqtt/config.yaml
mqtt_host: homeassistant.local
mqtt_username: user
mqtt_password: pass
friendly_name: aircontrol-mini
EOF

# Add systemd service

SERVICE_PATH=/lib/systemd/system/${SRVNAME}.service

cat <<'EOF' > $SERVICE_PATH
[Unit]
Description="zytempmqtt service"
Documentation=https://github.com/patrislav1/zytemp_mqtt
After=network.target
StopWhenUnneeded=false
StartLimitIntervalSec=10
StartLimitInterval=10
StartLimitBurst=3
[Service]
Type=simple
User=zytempmqtt
Group=zytempmqtt
Restart=always
RestartSec=10
ExecStart=/usr/bin/python3 -m zytempmqtt
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
