import logging
import asyncio

import voluptuous as vol

from homeassistant.components.light import (PLATFORM_SCHEMA, Light, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS,
                                            SUPPORT_BRIGHTNESS, SUPPORT_RGB_COLOR, SUPPORT_WHITE_VALUE)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME)

from ..ampio import unpack_item_address

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ampio'

CONF_ITEM = 'item'
CONF_BRIGHT_ITEM = 'bright_item'
CONF_RGB_ITEM = 'rgb_item'
CONF_WHITE_ITEM = 'white_item'
ATTR_MODULE_NAME = 'module_name'
ATTR_MODULE_PART_NUMBER = 'module_part_number'
ATTR_CAN_ID = 'can_id'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Optional(CONF_BRIGHT_ITEM): unpack_item_address,
    vol.Optional(CONF_RGB_ITEM): unpack_item_address,
    vol.Optional(CONF_WHITE_ITEM): unpack_item_address,
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
        async_add_devices([AmpioLight(hass, config)])
    return True


class AmpioLight(Light):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.ampio = hass.data[DOMAIN]
        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)
        self._supported_features = 0
        self._attributes = {}

        if CONF_BRIGHT_ITEM in config:
            self.ampio.register_on_value_change_callback(*config[CONF_BRIGHT_ITEM], callback=self.schedule_update_ha_state)
            self._supported_features |= SUPPORT_BRIGHTNESS

        if CONF_RGB_ITEM in config:
            self._supported_features |= SUPPORT_RGB_COLOR
            self.ampio.register_on_value_change_callback(*config[CONF_RGB_ITEM], callback=self.schedule_update_ha_state)

        if CONF_WHITE_ITEM in config:
            self._supported_features |= SUPPORT_WHITE_VALUE
            self.ampio.register_on_value_change_callback(*config[CONF_WHITE_ITEM], callback=self.schedule_update_ha_state)

        if CONF_FRIENDLY_NAME in config:
            self._attributes[ATTR_FRIENDLY_NAME] = config[CONF_FRIENDLY_NAME]

        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(config[CONF_ITEM][0])
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(config[CONF_ITEM][0])
        self._attributes[ATTR_CAN_ID] = config[CONF_ITEM][0]

    @property
    def is_on(self):
        state = False
        can_id, _, index = self.config[CONF_ITEM]
        if self._supported_features & SUPPORT_RGB_COLOR:
            red = self.ampio.get_item_state(can_id, "bin_red", index)
            green = self.ampio.get_item_state(can_id, "bin_green", index)
            blue = self.ampio.get_item_state(can_id, "bin_blue", index)
            state = red or green or blue

        state = state or self.ampio.get_item_state(can_id, "bin_output", index)
        return state

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        """No polling needed within Ampio."""
        return False

    @property
    def brightness(self):
        return self.ampio.get_item_state(*self.config[CONF_BRIGHT_ITEM]) \
            if self._supported_features & SUPPORT_BRIGHTNESS else None

    @property
    def rgb_color(self):
        if not self._supported_features & SUPPORT_RGB_COLOR:
            return None, None, None

        can_id, _, index = self.config[CONF_RGB_ITEM]
        red = self.ampio.get_item_state(can_id, "color_red", index)
        green = self.ampio.get_item_state(can_id, "color_green", index)
        blue = self.ampio.get_item_state(can_id, "color_blue", index)
        return red, green, blue

    @property
    def white_value(self):
        """Return the white value of this light between 0..255."""
        return self.ampio.get_item_state(*self.config[CONF_WHITE_ITEM]) \
            if self._supported_features & SUPPORT_WHITE_VALUE else None

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def turn_on(self, **kwargs):
        pass

    def turn_off(self, **kwargs):
        pass
