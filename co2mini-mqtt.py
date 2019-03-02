from CO2Meter import CO2Meter, CO2METER_CO2, CO2METER_HUM, CO2METER_TEMP
from paho.mqtt.client import Client
import platform, json, time, yaml


SOURCE_MAP = {
    CO2METER_CO2: 'co2',
    CO2METER_TEMP: 'temperature',
    CO2METER_HUM: 'humidity',
}


class Co2miniMqtt:
    def __init__(self, config="config.yml"):
        self.config = yaml.load(open(config, 'r').read())
        self.prefix = "/".join((self.config.get('mqtt', {}).get('discovery_prefix', 'homeassistant'), 'sensor', platform.node(), self.config.get('object_id', 'co2mini')))
        self.sensor = None
        self.mqttc = None
        self.state = {}

    def main(self):
        self.mqttc = Client()
        self.mqttc.will_set("{}/status".format(self.prefix), 'offline', retain=True)
        self.mqttc.enable_logger()
        self.mqttc.username_pw_set(self.config.get('mqtt', {}).get('username', 'homeassistant'), self.config.get('mqtt', {}).get('password', ''))
        self.mqttc.connect(self.config.get('mqtt', {}).get('broker', '127.0.0.1'), port=self.config.get('mqtt', {}).get('port', 1883), keepalive=self.config.get('mqtt', {}).get('keepalive', 60))
        self.mqttc.loop_start()

        disc_config = {
            'state_topic': "{}/state".format(self.prefix),
            'expire_after': 10,
            'name': self.config.get('name', '{} co2mini'.format(platform.node())),
            'unit_of_measurement': 'ppm',
            'icon': 'mdi:periodic-table-co2',
            'value_template': "{{ value_json.co2 }}",
            'availability_topic': "{}/status".format(self.prefix),
            'payload_available': "online",
            'payload_not_available': "offline",
            'json_attributes_topic': "{}/state".format(self.prefix),
            'force_update': True,
            'unique_id': '{}:{}'.format(platform.node(), self.config.get('device', '/dev/co2mini0')),
            'device': {
                'connections': [
                    ['usb', self.config.get('device', '/dev/co2mini0')],
                ]
            }
        }

        self.mqttc.publish("{}/config".format(self.prefix), json.dumps(disc_config), retain=True)

        self.sensor = CO2Meter(self.config.get('device', '/dev/co2mini0'), self.sensor_callback)
        self.mqttc.publish("{}/status".format(self.prefix), 'online', retain=True)

        while True:
            time.sleep(10)

    def sensor_callback(self, sensor, value):
        self.state[SOURCE_MAP[sensor]] = value
        self.mqttc.publish("{}/state".format(self.prefix), json.dumps(self.state), retain=True)


if __name__ == "__main__":
    Co2miniMqtt().main()
