import logging
import asyncio

import voluptuous as vol

from homeassistant.components.climate import (PLATFORM_SCHEMA, ClimateDevice, TEMP_CELSIUS,
                                              SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_HUMIDITY,
                                              SUPPORT_TARGET_HUMIDITY_HIGH, SUPPORT_TARGET_HUMIDITY_LOW)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME)

from ..ampio import unpack_item_address

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ampio'

CONF_ITEM = 'item'
CONF_HUMIDITY_ITEM = 'humidity_item'

ATTR_MODULE_NAME = 'module_name'
ATTR_MODULE_PART_NUMBER = 'module_part_number'
ATTR_CAN_ID = 'can_id'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Optional(CONF_HUMIDITY_ITEM): unpack_item_address,
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
        async_add_devices([AmpioClimate(hass, config)])
    return True


class AmpioClimate(ClimateDevice):
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.ampio = hass.data[DOMAIN]
        self._can_id = config[CONF_ITEM][0]
        self._index = config[CONF_ITEM][2]

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)

        self._attributes = {}
        self._supported_features = SUPPORT_TARGET_TEMPERATURE

        if CONF_FRIENDLY_NAME in config:
            self._attributes[ATTR_FRIENDLY_NAME] = config[CONF_FRIENDLY_NAME]

        if CONF_HUMIDITY_ITEM in config:
            self.ampio.register_on_value_change_callback(*config[CONF_HUMIDITY_ITEM], callback=self.schedule_update_ha_state)
            self._supported_features |= SUPPORT_TARGET_HUMIDITY | SUPPORT_TARGET_HUMIDITY_HIGH | SUPPORT_TARGET_HUMIDITY_LOW

        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(config[CONF_ITEM][0])
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(config[CONF_ITEM][0])
        self._attributes[ATTR_CAN_ID] = config[CONF_ITEM][0]

    @property
    def name(self):
        return self._name

    @property
    def should_poll(self):
        """No polling needed within Ampio."""
        return False

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        try:
            return self.ampio.get_item_state(self._can_id, 'measured', self._index)
        except TypeError:
            return None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        try:
            return self.ampio.get_item_state(self._can_id, 'setpoint', self._index)
        except TypeError:
            return None

    @property
    def target_humidity(self):
        return 50

    @property
    def current_humidity(self):
        """Return the current humidity."""
        try:
            return self.ampio.get_item_state(*self.config[CONF_HUMIDITY_ITEM])
        except (TypeError, KeyError):
            return None


    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features
        support = SUPPORT_TARGET_TEMPERATURE
        return support

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def set_temperature(self, **kwargs):
        pass

    def set_humidity(self, humidity):
        pass
