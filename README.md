````
pip3 install -r requirements.txt
[ -f /etc/udev/rules.d/90-co2mini.rules ] || sudo tee -a /etc/udev/rules.d/90-co2mini.rules <<EOF
ACTION=="remove", GOTO="co2mini_end"

SUBSYSTEMS=="usb", KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="a052", GROUP="plugdev", MODE="0660", SYMLINK+="co2mini%n", GOTO="co2mini_end"

LABEL="co2mini_end"
EOF
sudo udevadm trigger
sudo loginctl enable-linger $(whoami)
systemctl --user enable $(pwd)/co2mini-mqtt.service

# Recommended: create and edit config.yml

systemctl --user start co2mini-mqtt.service
````

