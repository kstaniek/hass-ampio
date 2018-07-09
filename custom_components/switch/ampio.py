import logging
import asyncio

import voluptuous as vol

from homeassistant.components.switch import (PLATFORM_SCHEMA, SwitchDevice)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME)

from homeassistant.core import callback

from ..ampio import unpack_item_address, Ampio

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['ampio']

DOMAIN = 'ampio'

CONF_ITEM = 'item'
CONF_ITEMS = 'items'
ATTR_MODULE_NAME = 'module_name'
ATTR_MODULE_PART_NUMBER = 'module_part_number'
ATTR_CAN_ID = 'can_id'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
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
        async_add_devices([AmpioSwitch(hass, config)])
    return True

@callback
def async_add_devices_discovery(hass, discovery_info, async_add_devices):
    """Setup AmpioSensor from discovery data."""
    items = discovery_info[CONF_ITEMS]
    for item in items:
        async_add_devices([AmpioSwitch(hass, item)])



class AmpioSwitch(SwitchDevice):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.ampio = hass.data[DOMAIN]
        self._can_id = config[CONF_ITEM][0]
        self._index = config[CONF_ITEM][2]

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)
        self._attributes = dict()
        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(self._can_id)
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(self._can_id)
        self._attributes[ATTR_CAN_ID] = "{:08x}".format(self._can_id)

    @property
    def is_on(self):
        return self.ampio.get_item_state(*self.config[CONF_ITEM])

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        """No polling needed within Ampio."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    async def async_turn_on(self, **kwargs):
        """Turn on."""
        await self.ampio.send_value_with_index(self._can_id, self._index, 0xff)

    async def async_turn_off(self, **kwargs):
        """Turn off."""
        await self.ampio.send_value_with_index(self._can_id, self._index, 0x00)
