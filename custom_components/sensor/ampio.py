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

from ..ampio import ATTR_DISCOVER_ITEMS

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
    vol.Required(CONF_ITEM): cv.string,
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
        self.ampio = hass.data[DOMAIN]
        self.hass = hass

        item = config[CONF_ITEM]
        can_id, self.attribute, index = item.split('/')
        self.can_id = int(can_id, 0)
        self.index = int(index, 0)

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(self.can_id, self.attribute, self.index))
        self._device_class = config.get(CONF_DEVICE_CLASS, None)
        self._attributes = {}

        if CONF_FRIENDLY_NAME in config:
            self._attributes = {
                ATTR_FRIENDLY_NAME: config[CONF_FRIENDLY_NAME],
            }

        # TODO: implement API
        # self._attributes.update(module_name=self.module_manager.get_module(can_id).name)

        self.ampio.register_on_value_change_callback(
            can_id=self.can_id,
            attribute=self.attribute,
            index=self.index,
            callback=self.schedule_update_ha_state
        )

    @property
    def state(self):
        return self.ampio.get_item_state(self.can_id, self.attribute, self.index)

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
        # TODO: Implement API in pyampio to get the unit
        return None

    # @property
    # def device_class(self):
    #     """Return the class of this sensor."""
    #     return self._device_class
