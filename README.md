````
sudo loginctl enable-linger $(whoami)
systemctl --user enable $(pwd)/co2mini-mqtt.service
systemctl --user start co2mini-mqtt.service
````

