import logging
import asyncio
from enum import Enum

import voluptuous as vol

from homeassistant.components.climate import (PLATFORM_SCHEMA, ClimateDevice, TEMP_CELSIUS,
                                              SUPPORT_TARGET_TEMPERATURE, SUPPORT_TARGET_HUMIDITY,
                                              SUPPORT_TARGET_HUMIDITY_HIGH, SUPPORT_TARGET_HUMIDITY_LOW,
                                              SUPPORT_OPERATION_MODE, SUPPORT_ON_OFF)

import homeassistant.helpers.config_validation as cv

from homeassistant.const import (CONF_NAME, CONF_FRIENDLY_NAME, STATE_UNKNOWN, ATTR_FRIENDLY_NAME, STATE_ON, STATE_OFF)

from ..ampio import unpack_item_address

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'ampio'

CONF_ITEM = 'item'
CONF_TARGET_ITEM = 'target_item'
CONF_HUMIDITY_ITEM = 'humidity_item'
CONF_OPERATION_MODE_ITEM = 'operation_mode_item'

ATTR_MODULE_NAME = 'module_name'
ATTR_MODULE_PART_NUMBER = 'module_part_number'
ATTR_CAN_ID = 'can_id'

"""
0 - Auto
1 - Manual
2 - Semi
3 - Holiday
4 - Blocked
"""


class OperationMode(Enum):
    Auto = 0
    Manual = 16
    Semi = 32
    Holiday = 48
    Blocked = 64


OPERATION_MODE_LIST = [mode.name for mode in OperationMode]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Required(CONF_TARGET_ITEM): unpack_item_address,
    vol.Optional(CONF_HUMIDITY_ITEM): unpack_item_address,
    vol.Optional(CONF_OPERATION_MODE_ITEM): unpack_item_address,
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
        self._supported_features = 0

        if CONF_TARGET_ITEM in config:
            self._supported_features |= SUPPORT_TARGET_TEMPERATURE
            self.ampio.register_on_value_change_callback(*config[CONF_TARGET_ITEM], callback=self.schedule_update_ha_state)


        if CONF_HUMIDITY_ITEM in config:
            self.ampio.register_on_value_change_callback(*config[CONF_HUMIDITY_ITEM], callback=self.schedule_update_ha_state)
            self._supported_features |= SUPPORT_TARGET_HUMIDITY | SUPPORT_TARGET_HUMIDITY_HIGH | SUPPORT_TARGET_HUMIDITY_LOW

        if CONF_OPERATION_MODE_ITEM in config:
            self.ampio.register_on_value_change_callback(*config[CONF_OPERATION_MODE_ITEM],
                                                         callback=self.schedule_update_ha_state)
            self._supported_features |= SUPPORT_OPERATION_MODE

        if CONF_FRIENDLY_NAME in config:
            self._attributes[ATTR_FRIENDLY_NAME] = config[CONF_FRIENDLY_NAME]

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
    def is_on(self):
        return False

    # @property
    # def state(self):
    #     print("STATE CALLED")
    #     """Return the current state."""
    #     if self.is_on is False:
    #         return STATE_OFF
    #     if self.current_operation:
    #         return self.current_operation
    #     if self.is_on:
    #         return STATE_ON
    #     return STATE_UNKNOWN

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
        if self._supported_features & SUPPORT_TARGET_TEMPERATURE:
            try:
                return self.ampio.get_item_state(self._can_id, 'setpoint', self._index)
            except TypeError:
                return None
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
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._supported_features & SUPPORT_OPERATION_MODE:
            try:
                return OperationMode(self.ampio.get_item_state(*self.config[CONF_OPERATION_MODE_ITEM])).name
            except (TypeError, KeyError, ValueError):
                return None
        else:
            return None
    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return OPERATION_MODE_LIST

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        pass

    def set_humidity(self, humidity):
        """Set new target humidity."""
        pass

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""

