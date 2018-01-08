
import asyncio
import logging

import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING, STATE_ALARM_TRIGGERED, STATE_UNKNOWN, STATE_ALARM_ARMING,
    CONF_NAME, CONF_CODE, CONF_FRIENDLY_NAME, ATTR_FRIENDLY_NAME)

from ..ampio import unpack_item_address, ATTR_MODULE_NAME, ATTR_MODULE_PART_NUMBER, ATTR_CAN_ID

STATE_ALARM_ARMING_10s = 'Arming(10s)'


_LOGGER = logging.getLogger(__name__)

DOMAIN = "ampio"

CONF_ITEM = 'item'
CONF_ZONES = 'zones'

"""
  - platform: ampio
    name: a_ground_floor
    item: 0x00001ecc/*/1
    friendly_name: Strefa Parteru
  
  - platform: ampio
    name: a_upper_floor
    item: 0x00001ecc/*/2
    friendly_name: Strefa Piętra
  
  - platform: ampio
    name: a_outside
    item: 0x00001ecc/*/3
    friendly_name: Strefa Zewnętrzna
  
"""

PLATFORM_SCHEMA = alarm.PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ITEM): unpack_item_address,
    vol.Optional(CONF_FRIENDLY_NAME, default=None): cv.string,
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    # TODO: This should be removed when pyampio refactored to allow callback register before discovery
    while DOMAIN not in hass.data or not hass.data[DOMAIN].state.value == 8:
        yield

    if discovery_info is None:
        async_add_devices([AmpioSatelAlarm(hass, config)])
    pass


class AmpioSatelAlarm(alarm.AlarmControlPanel):
    def __init__(self, hass, config):
        self.hass = hass
        self.ampio = hass.data[DOMAIN]
        self.config = config

        self._can_id = config[CONF_ITEM][0]
        self._index = config[CONF_ITEM][2]

        self._name = config.get(CONF_NAME, "{:08x}_{}_{}".format(*config[CONF_ITEM]))
        self.ampio.register_on_value_change_callback(*config[CONF_ITEM], callback=self.schedule_update_ha_state)

        self._attributes = {}

        if CONF_FRIENDLY_NAME in config:
            self._attributes = {
                ATTR_FRIENDLY_NAME: config[CONF_FRIENDLY_NAME],
            }

        self._attributes[ATTR_MODULE_NAME] = self.ampio.get_module_name(self._can_id)
        self._attributes[ATTR_MODULE_PART_NUMBER] = self.ampio.get_module_part_number(self._can_id)
        self._attributes[ATTR_CAN_ID] = "{:08x}".format(self._can_id)


    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def state(self):
        _state = STATE_UNKNOWN

        if self.ampio.get_item_state(self._can_id, 'alarm', self._index):
            _state = STATE_ALARM_TRIGGERED
        else:
            _state = STATE_ALARM_DISARMED

        if self.ampio.get_item_state(self._can_id, 'armed', self._index):
            _state = STATE_ALARM_ARMED_AWAY

        if self.ampio.get_item_state(self._can_id, 'arming', self._index):
            _state = STATE_ALARM_ARMING

        if self.ampio.get_item_state(self._can_id, 'arming10s', self._index):
            _state = STATE_ALARM_ARMING_10s

        if self.ampio.get_item_state(self._can_id, 'breached', self._index):
            _state = STATE_ALARM_PENDING

        return _state

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        # TODO: Implement
        pass

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        # TODO: Implement
        pass

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        # TODO: Implement
        pass

    def alarm_arm_night(self, code=None):
        """Send arm night command."""
        pass
