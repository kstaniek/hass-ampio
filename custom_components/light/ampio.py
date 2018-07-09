import logging
import asyncio

import voluptuous as vol

from homeassistant.components.light import (PLATFORM_SCHEMA, Light, ATTR_BRIGHTNESS, ATTR_RGB_COLOR, ATTR_WHITE_VALUE,
                                            SUPPORT_BRIGHTNESS, SUPPORT_COLOR, SUPPORT_WHITE_VALUE,
                                            ATTR_HS_COLOR)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME)
import homeassistant.util.color as color_util

from ..ampio import unpack_item_address, Ampio

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ampio'


DEPENDENCIES = ['ampio']

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
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    # TODO: This should be removed when pyampio refactored to allow callback register before discovery
    while DOMAIN not in hass.data or not hass.data[DOMAIN].is_ready:
        yield

    if discovery_info is not None:
        return True
    else:
        async_add_devices([AmpioLight(hass, config)])
    return True


class AmpioLight(Ampio, Light):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.ampio = hass.data[DOMAIN]
        self._can_id = config[CONF_ITEM][0]
        self._index = config[CONF_ITEM][2]
        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)
        self._supported_features = 0
        self._attributes = {}
        self._last_brightness = 0xff
        self._last_rgb_color = (0xff, 0xff, 0xff)
        self._last_white_value = 0xff

        if CONF_BRIGHT_ITEM in config:
            self.ampio.register_on_value_change_callback(*config[CONF_BRIGHT_ITEM], callback=self.schedule_update_ha_state)
            self._supported_features |= SUPPORT_BRIGHTNESS

        if CONF_RGB_ITEM in config:
            self._supported_features |= SUPPORT_COLOR
            self.ampio.register_on_value_change_callback(*config[CONF_RGB_ITEM], callback=self.schedule_update_ha_state)

        if CONF_WHITE_ITEM in config:
            self._supported_features |= SUPPORT_WHITE_VALUE
            self.ampio.register_on_value_change_callback(*config[CONF_WHITE_ITEM], callback=self.schedule_update_ha_state)

        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(self._can_id)
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(self._can_id)
        self._attributes[ATTR_CAN_ID] = "{:08x}".format(self._can_id)

    @property
    def is_on(self):
        state = False
        can_id, _, index = self.config[CONF_ITEM]
        if self._supported_features & SUPPORT_COLOR:
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
    def last_brightness(self):
        brightness = self.ampio.get_item_last_state(*self.config[CONF_BRIGHT_ITEM])
        return 0xff if brightness is None or brightness == 0x00 else brightness

    @property
    def rgb_color(self):
        if not self._supported_features & SUPPORT_COLOR:
            return  # None, None, None

        red = self.ampio.get_item_state(self._can_id, "color_red", self._index)
        green = self.ampio.get_item_state(self._can_id, "color_green", self._index)
        blue = self.ampio.get_item_state(self._can_id, "color_blue", self._index)
        return red, green, blue

    # TODO: Redesign PyAmpio
    # This does not work properly beacuse pyampio must have additional abstraction layer
    # to map atomic item like rgb (r,g,b) tuple into the broadcast to be able to
    # store the last value as the whole tuple.
    # The item bust be decoupled from broadcast and the last value must be stored as last item
    # value not as last broadcast.
    # @property
    # def last_rgb_color(self):
    #     if not self._supported_features & SUPPORT_RGB_COLOR:
    #         return 0, 0, 0
    #
    #     red = self.ampio.get_item_last_state(self._can_id, "color_red", self._index)
    #     green = self.ampio.get_item_last_state(self._can_id, "color_green", self._index)
    #     blue = self.ampio.get_item_last_state(self._can_id, "color_blue", self._index)
    #     print("RGB LAST STATE={},{},{}".format(red, green, blue))
    #
    #     red = 0xff if red is None else red
    #     green = 0xff if green is None else green
    #     blue = 0xff if blue is None else blue
    #
    #     return red, green, blue

    @property
    def white_value(self):
        """Return the white value of this light between 0..255."""
        return self.ampio.get_item_state(*self.config[CONF_WHITE_ITEM]) \
            if self._supported_features & SUPPORT_WHITE_VALUE else None

    @property
    def last_white_value(self):
        """Return the white value of this light between 0..255."""
        if not self._supported_features & SUPPORT_WHITE_VALUE:
            return None

        white = self.ampio.get_item_last_state(*self.config[CONF_WHITE_ITEM])
        if white is None:
            return 0xff

        if (not self._supported_features & SUPPORT_COLOR or self.last_rgb_color == (0, 0, 0)) and white == 0x00:
            return 0xff

        return white

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    async def async_turn_on(self, **kwargs):
        """Turn the specific light on."""
        value_sent = False

        if ATTR_HS_COLOR in kwargs:
            rgb = color_util.color_hs_to_RGB(*kwargs[ATTR_HS_COLOR])
            await self.ampio.send_rgb_values(self._can_id, *rgb)
            value_sent = True

        if ATTR_RGB_COLOR in kwargs:
            await self.ampio.send_rgb_values(self._can_id, *kwargs[ATTR_RGB_COLOR])
            value_sent = True

        if ATTR_WHITE_VALUE in kwargs:
            await self.ampio.send_white_value(self._can_id, kwargs[ATTR_WHITE_VALUE])
            value_sent = True

        if ATTR_BRIGHTNESS in kwargs:
            await self.ampio.send_value_with_index(self._can_id, self._index, kwargs[ATTR_BRIGHTNESS])
            value_sent = True

        if value_sent:
            # Return if there was any value in kwargs to be sent.
            return

        if self._supported_features & SUPPORT_COLOR:
            await self.ampio.send_rgb_values(self._can_id, *self._last_rgb_color)

        if self._supported_features & SUPPORT_WHITE_VALUE:
            await self.ampio.send_white_value(self._can_id, self._last_white_value)

        if self._supported_features & SUPPORT_BRIGHTNESS:
            await self.ampio.send_value_with_index(self._can_id, self._index, self._last_white_value)

        if self._supported_features == 0:
            await self.ampio.send_value_with_index(self._can_id, self._index, 0xff)

    async def async_turn_off(self, **kwargs):
        if self._supported_features & SUPPORT_COLOR:
            self._last_rgb_color = self.rgb_color
            self._last_white_value = self.white_value
            await self.ampio.send_rgb_values(self._can_id, 0, 0, 0)
            await self.ampio.send_white_value(self._can_id, 0)
            return

        elif self._supported_features & SUPPORT_BRIGHTNESS:
            self._last_brightness = self.brightness if \
                (self.brightness is not 0x00) and (self.brightness is not None) else 0xff

        await self.ampio.send_value_with_index(self._can_id, self._index, 0x00)
