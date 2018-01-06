import asyncio
import logging

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_DEVICE_CLASS, CONF_ENTITY_ID, CONF_NAME,
    STATE_UNKNOWN, CONF_FRIENDLY_NAME,ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME)
from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA, PLATFORM_SCHEMA, BinarySensorDevice)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.core import callback

from ..ampio import unpack_item_address

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ampio"


CONF_CAN_ID = "can_id"
CONF_MODULE = "module"
CONF_BIN_INPUT = "bin_input"
CONF_BIN_OUTPUT = "bin_output"
CONF_INPUT = "input"
CONF_OUTPUT = "output"
CONF_INDEX = "index"
CONF_ITEMS = "items"
CONF_ITEM = "item"
CONF_TYPE = "type"



"""
sensor:
  - platform: ampio
    name: optional1
    item: 0x1ecc/bin_input/1
    device_class: motion
    friendly_name: Input 1

  - platform: ampio
    name: optional2
    item: 0x1ecc/bin_input/2
    device_class: motion
    friendly_name: Input 2


"""


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Optional(CONF_NAME, default=None): cv.string,
    vol.Optional(CONF_TYPE): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME, default=None): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    # TODO: This should be removed when pyampio refactored to allow callback register before discovery
    while DOMAIN not in hass.data or not hass.data[DOMAIN].state.value == 8:
        yield

    if discovery_info is not None:
        async_add_devices_discovery(hass, discovery_info, async_add_devices)
    else:
        async_add_devices([AmpioSensor(hass, config)])

    return True


@callback
def async_add_devices_discovery(hass, discovery_info, async_add_devices):
    """Setup AmpioSensor from discovery data."""
    items = discovery_info[CONF_ITEMS]
    for item in items:
        async_add_devices([AmpioSensor(hass, item)])


class AmpioSensor(Entity):

    def __init__(self, hass, config):
        self.hass = hass
        self.ampio = hass.data[DOMAIN]
        self.config = config

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)
        self._device_class = config.get(CONF_DEVICE_CLASS, None)
        self._attributes = {}

        if CONF_FRIENDLY_NAME in config:
            self._attributes = {
                ATTR_FRIENDLY_NAME: config[CONF_FRIENDLY_NAME],
            }
        else:
            self._attributes = {
                ATTR_FRIENDLY_NAME: self.ampio.get_module_name(config[CONF_ITEM][0]),
            }


    @property
    def state(self):
        return self.ampio.get_item_state(*self.config[CONF_ITEM])

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for Ampio"""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self.ampio.get_item_measurement_unit(*self.config[CONF_ITEM])
