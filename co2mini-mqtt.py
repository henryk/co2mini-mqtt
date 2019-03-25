from CO2Meter_mod import CO2Meter_mod as CO2Meter, CO2METER_CO2, CO2METER_HUM, CO2METER_TEMP
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
        self.disc_config = {}
        self.alive = True
        self.last_pub = {}

    def on_connect(self, *args, **kwargs):
        self.mqttc.publish("{}/config".format(self.prefix), json.dumps(self.disc_config), retain=True)

        self.mqttc.publish("{}/status".format(self.prefix), 'online', retain=True)

    def main(self):
        self.mqttc = Client()
        self.mqttc.will_set("{}/status".format(self.prefix), 'offline', retain=True)
        self.mqttc.enable_logger()
        self.mqttc.username_pw_set(self.config.get('mqtt', {}).get('username', 'homeassistant'), self.config.get('mqtt', {}).get('password', ''))
        self.mqttc.on_connect = self.on_connect

        self.disc_config = {
            'state_topic': "{}/state".format(self.prefix),
            #'expire_after': 10,
            'name': self.config.get('name', '{} co2mini'.format(platform.node())),
            'unit_of_measurement': 'ppm',
            'icon': 'mdi:periodic-table-co2',
            'availability_topic': "{}/status".format(self.prefix),
            'payload_available': "online",
            'payload_not_available': "offline",
            'json_attributes_topic': "{}/attributes".format(self.prefix),
            'force_update': self.config.get('force_update', False),
            'unique_id': '{}:{}'.format(platform.node(), self.config.get('device', '/dev/co2mini0')),
            'device': {
                'connections': [
                    ['usb', self.config.get('device', '/dev/co2mini0')],
                ],
                'identifiers':
                    ('dns', platform.node()),
                'manufacturer': 'Various',
                'model': 'co2mini',
            }
        }

        self.sensor = CO2Meter(self.config.get('device', '/dev/co2mini0'), self.sensor_callback)

        self.mqttc.connect(self.config.get('mqtt', {}).get('broker', '127.0.0.1'), port=self.config.get('mqtt', {}).get('port', 1883), keepalive=self.config.get('mqtt', {}).get('keepalive', 60))
        self.mqttc.loop_start()

        while self.alive:
            self.alive = False
            time.sleep(10)

    def sensor_callback(self, sensor, value):
        self.state[SOURCE_MAP[sensor]] = value
        pub = {
           'state': self.state.get('co2'),
           'attributes': json.dumps({k:v for (k,v) in self.state.items() if not k == 'co2'}),
        }
        for k, v in pub.items():
            if v != self.last_pub.get(k, None):
               self.mqttc.publish("{}/{}".format(self.prefix, k), v, retain=True)
               self.last_pub[k] = v
        self.alive = True


if __name__ == "__main__":
    Co2miniMqtt().main()
