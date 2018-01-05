import logging
import asyncio

import voluptuous as vol

from homeassistant.components.cover import (PLATFORM_SCHEMA, CoverDevice, SUPPORT_OPEN, SUPPORT_CLOSE, SUPPORT_STOP,
                                            SUPPORT_OPEN_TILT, SUPPORT_CLOSE_TILT, SUPPORT_STOP_TILT)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME)

from ..ampio import unpack_item_address

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ampio'

CONF_ITEM = 'item'
CONF_TILT_ITEM = 'tilt_item'

ATTR_MODULE_NAME = 'module_name'
ATTR_MODULE_PART_NUMBER = 'module_part_number'
ATTR_CAN_ID = 'can_id'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Optional(CONF_TILT_ITEM): unpack_item_address,
    vol.Optional(CONF_FRIENDLY_NAME, default=None): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    # TODO: This should be removed when pyampio refactored to allow callback register before discovery
    while DOMAIN not in hass.data or not hass.data[DOMAIN].state.value == 8:
        yield

    if discovery_info is not None:
        return True
    else:
        async_add_devices([AmpioCover(hass, config)])
    return True


class AmpioCover(CoverDevice):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.ampio = hass.data[DOMAIN]
        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self._supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

        self._can_id = config[CONF_ITEM][0]
        self._index = config[CONF_ITEM][2]
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)
        self.ampio.register_on_value_change_callback(self._can_id, 'opening', self._index, callback=self.schedule_update_ha_state)
        self.ampio.register_on_value_change_callback(self._can_id, 'closing', self._index, callback=self.schedule_update_ha_state)

        if CONF_TILT_ITEM in config:
            self._supported_features |= SUPPORT_OPEN_TILT | SUPPORT_CLOSE_TILT | SUPPORT_STOP_TILT
            self.ampio.register_on_value_change_callback(*config[CONF_TILT_ITEM], callback=self.schedule_update_ha_state)

        self._attributes = {}

        if CONF_FRIENDLY_NAME in config:
            self._attributes[ATTR_FRIENDLY_NAME] = config[CONF_FRIENDLY_NAME]

        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(config[CONF_ITEM][0])
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(config[CONF_ITEM][0])
        self._attributes[ATTR_CAN_ID] = config[CONF_ITEM][0]

    @property
    def is_closed(self):
        state = (self.current_cover_position == 0)
        if self.current_cover_tilt_position is not None:
            state = state and (self.current_cover_tilt_position == 0)

        return state

    @property
    def is_opening(self):
        return self.ampio.get_item_state(self._can_id, 'opening', self._index)

    @property
    def is_closing(self):
        return self.ampio.get_item_state(self._can_id, 'closing', self._index)

    @property
    def current_cover_position(self):
        return self.ampio.get_item_state(*self.config[CONF_ITEM])

    @property
    def current_cover_tilt_position(self):
        if CONF_TILT_ITEM in self.config:
            return self.ampio.get_item_state(*self.config[CONF_TILT_ITEM])
        else:
            return None

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

    def open_cover(self, **kwargs):
        pass

    def close_cover(self, **kwargs):
        pass

    def stop_cover(self, **kwargs):
        pass

    def open_cover_tilt(self, **kwargs):
        pass

    def close_cover_tilt(self, **kwargs):
        pass

    def stop_cover_tilt(self, **kwargs):
        pass

