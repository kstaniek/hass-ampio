import logging
import re
import json
import asyncio
import aiohttp
import async_timeout

import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import (CONF_IP_ADDRESS, ATTR_ATTRIBUTION)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): vol.Coerce(str)
})

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = 'Data provided by Ampio Smog Sensor'

ATTR_PM10 = 'pm_10'
ATTR_PM2_5 = 'pm_2_5'
ATTR_PM1 = 'pm_1'
ATTR_PRESSURE = 'pressure'
ATTR_HUMIDITY = 'humidity'

KEY_TO_ATTR = {
    'PM1': ATTR_PM1,
    'PM2.5': ATTR_PM2_5,
    'PM10': ATTR_PM10,
    'Humidity': ATTR_HUMIDITY,
    'Pressure': ATTR_PRESSURE,
}


MIN_TIME_BETWEEN_UPDATES = 60
TIMEOUT = 10

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the AmpioSmog Sensor."""
    sensor_ip = config.get(CONF_IP_ADDRESS)
    client = SensorClient(sensor_ip=sensor_ip, session=async_get_clientsession(hass), timeout=TIMEOUT)
    sensor = AmpioSmog(client)
    async_add_devices([sensor], True)


class AmpioSmog(Entity):
    """Implementation of Ampio Smog Sensor."""

    def __init__(self, client):
        self.client = client
        self.data = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Ampio Smog Sensor"

    @property
    def icon(self):
        """Return icon."""
        return 'mdi:cloud'

    @property
    def state(self):
        if self.data:
            return self.data.get('PM10')
        return None

    @property
    def unit_of_measurement(self):
        """Return the measurement unit."""
        return "µg/m³"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the last update."""
        attrs = {}
        if self.data is not None:
            try:
                for key in self.data:
                    if key in KEY_TO_ATTR:
                        attrs[KEY_TO_ATTR[key]] = self.data[key]
                return attrs
            except (KeyError, IndexError):
                return {ATTR_ATTRIBUTION: ATTRIBUTION}

    @asyncio.coroutine
    def async_update(self):
        """Get the latest data."""
        self.data = yield from self.client.update()


class SensorClient(object):
    """Ampio Smog Sensor Client."""

    def __init__(self, sensor_ip, session=None, timeout=aiohttp.client.DEFAULT_TIMEOUT):
        """Initialize Sensor Client."""

        self.timeout = timeout
        self.api_url = f'http://{sensor_ip}/data'
        if session is not None:
            self.session = session
        else:
            self.session = aiohttp.ClientSession()

    @asyncio.coroutine
    def update(self):
        with async_timeout.timeout(self.timeout):
            response = yield from self.session.get(
                self.api_url
            )
            data = yield from response.text()
            data_dict = {key: int(value) for key, value in
                         dict(re.findall(r'(\S+)=(\d+)', data)).items()}
            try:
                data_dict['Humidity'] = data_dict['Humidity'] / 1000
                data_dict['Pressure'] = data_dict['Pressure'] / 100
            except KeyError:
                pass

            return data_dict
