import logging
import asyncio
import voluptuous as vol
from functools import partial
from collections import defaultdict

from homeassistant.helpers import config_validation as cv
from homeassistant.const import (CONF_PORT, CONF_FRIENDLY_NAME)
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "ampio"


REQUIREMENTS = ['pyampio==0.0.4']

CONF_AUTOCONFIG = 'autoconfig'
CONF_MODULE = 'module'
CONF_ITEMS = 'items'
CONF_ITEM = 'item'
CONF_USE_MODULE_NAME = 'use_module_name'
CONF_NAME = 'name'
CONF_BEGIN = 'begin'
CONF_END = 'end'

MODULES = ["MULTISENS"]


ATTR_DISCOVER_ITEMS = "items"

_LOGGER = logging.getLogger(__name__)


def unpack_item_address(value):
    can_id, attribute, index = value.split('/')
    can_id = int(can_id, 0)
    index = int(index, 0)
    return can_id, attribute, index


ITEMS_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_BEGIN): vol.Coerce(int),
    vol.Required(CONF_END): vol.Coerce(int),
})

AUTOCONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_ITEMS): [ITEMS_SCHEMA],
    vol.Required(CONF_MODULE): cv.string,
    vol.Optional(CONF_USE_MODULE_NAME): vol.Boolean,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(CONF_AUTOCONFIG): vol.All([AUTOCONFIG_SCHEMA]),
    }),
}, extra=vol.ALLOW_EXTRA)


is_discovered = False

item_to_sensor_map = {
    'temperature': 'sensor',
    'humidity': 'sensor',
    'mean-sea-level-pressure': 'sensor',
    'bin_input': 'binary_sensor',
    'alarm': 'binary_sensor',
    'armed': 'binary_sensor',
    'arming': 'binary_sensor',
    'arming10s': 'binary_sensor',
    'breached': 'binary_sensor',
}


def on_discovered(hass, config, modules):
    global is_discovered
    is_discovered = True
    _LOGGER.info("Ampio modules discovered.")
    items = defaultdict(list)
    if CONF_AUTOCONFIG in config[DOMAIN]:
        for can_id, mod in modules.modules.items():
            for details in config[DOMAIN][CONF_AUTOCONFIG]:
                module_name = details[CONF_MODULE]
                if module_name == mod.part_number:
                    for item in details[CONF_ITEMS]:
                        name = item[CONF_NAME]
                        component = item_to_sensor_map.get(name, None)
                        if component:
                            for i in range(item[CONF_BEGIN], item[CONF_END] + 1):
                                items[component].append({
                                    CONF_ITEM: "{}/{}/{}".format(can_id, name, i),
                                    CONF_FRIENDLY_NAME: name + "_{:03}".format(i),
                                })

    for component, details in items.items():
        hass.async_add_job(
            async_load_platform(hass, component, DOMAIN, {
                ATTR_DISCOVER_ITEMS: details
            }, config)
        )
    return


@asyncio.coroutine
def async_setup(hass, config):
    from pyampio.gateway import AmpioGateway

    port = config[DOMAIN].get(CONF_PORT)

    ampio_gw = AmpioGateway(port=port, loop=hass.loop)
    hass.data[DOMAIN] = ampio_gw
    ampio_gw.add_on_discovered_callback(partial(on_discovered, hass, config))

    while not is_discovered:
        yield

    return True
