import asyncio
import logging

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_DEVICE_CLASS, CONF_ENTITY_ID, CONF_NAME,
    STATE_UNKNOWN, CONF_FRIENDLY_NAME,ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME)
from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA, PLATFORM_SCHEMA, BinarySensorDevice)
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from ..ampio import unpack_item_address, ATTR_MODULE_NAME, ATTR_MODULE_PART_NUMBER, ATTR_CAN_ID, Ampio


_LOGGER = logging.getLogger(__name__)

DOMAIN = "ampio"


DEPENDENCIES = ['ampio']


CONF_CAN_ID = "can_id"
CONF_MODULE = "module"
CONF_BIN_INPUT = "bin_input"
CONF_BIN_OUTPUT = "bin_output"
CONF_INPUT = "input"
CONF_OUTPUT = "output"
CONF_INDEX = "index"
CONF_ITEMS = "items"
CONF_ITEM = "item"



"""
binary_sensor:
  platform: ampio
  module:
  - can_id: 0x1ecc
    items:
      bin_input:
        - index: 1
          friendly_name: Door
        - index: 2
          friendly_name: Window

binary_sensor:
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
    vol.Optional(CONF_DEVICE_CLASS): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    # TODO: This should be removed when pyampio refactored to allow callback register before discovery
    while DOMAIN not in hass.data or not hass.data[DOMAIN].is_ready:
        yield

    if discovery_info is not None:
        async_add_devices_discovery(hass, discovery_info, async_add_devices)
        return True
    else:
        async_add_devices([AmpioBinarySensor(hass, config)])

    return True


@callback
def async_add_devices_discovery(hass, discovery_info, async_add_devices):
    """Setup AmpioSensor from discovery data."""
    items = discovery_info[CONF_ITEMS]
    for item in items:
        async_add_devices([AmpioBinarySensor(hass, item)])


class AmpioBinarySensor(Ampio, BinarySensorDevice):

    def __init__(self, hass, config):
        self.hass = hass
        self.ampio = hass.data[DOMAIN]
        self.config = config

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*self.config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)

        self._device_class = config.get(CONF_DEVICE_CLASS, None)
        self._attributes = dict()
        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(config[CONF_ITEM][0])
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(config[CONF_ITEM][0])
        self._attributes[ATTR_CAN_ID] = config[CONF_ITEM][0]

    @property
    def is_on(self):
        return self.ampio.get_item_state(*self.config[CONF_ITEM])

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._device_class
