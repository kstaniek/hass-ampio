
import asyncio
import logging

import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING, STATE_ALARM_TRIGGERED, STATE_UNKNOWN, STATE_ALARM_ARMING,
    CONF_NAME, CONF_CODE, CONF_FRIENDLY_NAME, ATTR_FRIENDLY_NAME)


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
    vol.Required(CONF_ITEM): cv.string,
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
        # TODO: Add API pyampio to get ModuleManager
        self.module_manager = hass.data[DOMAIN]._modules
        self._name = config[CONF_NAME]
        self._states = {
            'armed': False,
            'alarm': False,
            'arming': False,
            'arming10s': False,
            'breached': False,
        }

        can_id, attribute, index = config[CONF_ITEM].split('/')
        can_id = int(can_id, 0)
        index = int(index, 0)

        self._attributes = {}

        if CONF_FRIENDLY_NAME in config:
            self._attributes = {
                ATTR_FRIENDLY_NAME: config[CONF_FRIENDLY_NAME],
            }

        self._attributes.update(module_name=self.module_manager.get_module(can_id).name)

        def on_zone_state_changed(modules, can_id, attribute, index, old_value, new_value, unit):
            self._states[attribute] = new_value
            self.schedule_update_ha_state()

        for attribute in self._states.keys():
            self.module_manager.add_on_value_changed_callback(
                can_id=can_id,
                attribute=attribute,
                index=index,
                callback=on_zone_state_changed
            )

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

        if self._states['alarm']:
            _state = STATE_ALARM_TRIGGERED
        else:
            _state = STATE_ALARM_DISARMED

        if self._states['armed']:
            _state = STATE_ALARM_ARMED_AWAY

        if self._states['arming']:
            _state = STATE_ALARM_ARMING

        if self._states['arming10s']:
            _state = STATE_ALARM_ARMING_10s

        if self._states['breached']:
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
