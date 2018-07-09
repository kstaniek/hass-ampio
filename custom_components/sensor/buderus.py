"""
Platform to read a Buderus KM200 unit.
"""
import logging
from datetime import timedelta

from custom_components.buderus import (
    DOMAIN, BuderusBridge)
from homeassistant.const import (
    CONF_RESOURCES, TEMP_CELSIUS, STATE_UNKNOWN)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['buderus']

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

SENSOR_TYPES = {}

"""
https://github.com/smarthomeNG/plugins/tree/master/buderus
ATTR_INFO_DATETIME
ATTR_INFO_FIRMWARE
ATTR_INFO_HARDWARE
ATTR_INFO_BRAND
ATTR_INFO_HEALTH
ATTR_OUTSIDE_TEMPERATURE
ATTR_SUPPLY_TEMPERATURE
ATTR_HOTWATER_TEMPERATURE
ATTR_BOILER_FLAME
ATTR_BOILER_STARTS
ATTR_HEATING_CURRENT_ROOMSETPOINT
ATTR_HEATING_MANUAL_ROOMSETPOINT
ATTR_HEATING_TEMP_SETPOINT
ATTR_HEATING_TEMP_ECO
ATTR_HEATING_TEMP_COMFORT
ATTR_HEATING_ACTIVEPROGRAM
ATTR_HEATING_MODE
         'hotwater_current_waterflow': [
            'Hotwater Waterflow',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/dhwCircuits/dhw1/waterFlow'
        ],
         'hotwater_current_workingtime': [
            'Hotwater Workingtime',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/dhwCircuits/dhw1/workingTime'
        ],
"""
"""
/system/appliance/flameCurrent
/system/appliance/ChimneySweeper
/system/appliance/workingTime
/system/appliance/nominalBurnerLoad
"""

def setup_platform(hass, config, add_devices, discovery_info=None):
    global SENSOR_TYPES
    SENSOR_TYPES = {
        'appliance_actual_supply_temp': [
            'Appliance Actual Supply Temp',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/appliance/actualSupplyTemperature'
        ],
        'appliance_power_setpoint': [
            'Appliance Power Setpoint',
            "%",
            'mdi:thermometer',
            '/system/appliance/powerSetpoint'
        ],
        'appliance_actual_power': [
            'Appliance Actual Power',
            "%",
            'mdi:thermometer',
            '/system/appliance/actualPower'
        ],
        'appliance_ch_pump_modulation': [
            'Appliance CH Pump Modulation',
            "%",
            'mdi:thermometer',
            '/system/appliance/CHpumpModulation'
        ],
        'appliance_number_of_starts': [
            'Appliance Number of Starts',
            "",
            'mdi:thermometer',
            '/system/appliance/numberOfStarts'
        ],
        'appliance_gas_air_pressure': [
            'Appliance Gas Air Pressure',
            "Pa",
            'mdi:thermometer',
            '/system/appliance/gasAirPressure'
        ],
        'appliance_system_pressure': [
            'Appliance System Pressure',
            "bar",
            'mdi:thermometer',
            '/system/appliance/systemPressure'
        ],
        'appliance_flame_current': [
            'Appliance Flame Current',
            "µA",
            'mdi:thermometer',
            '/system/appliance/flameCurrent'
        ],
        'appliance_chimney_sweeper': [
            'Appliance Chimney Sweeper',
            "",
            'mdi:thermometer',
            '/system/appliance/ChimneySweeper'
        ],
        'appliance_working_time_total_system': [
            'Appliance Total System Working Time',
            "",
            'mdi:thermometer',
            '/system/appliance/workingTime/totalSystem'
        ],
        'appliance_nominal_burner_load': [
            'Appliance Nominal Burner Load',
            "kW",
            'mdi:thermometer',
            '/system/appliance/nominalBurnerLoad'
        ],
        'outside_temperature': [
            'Outside Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/outdoor_t1'
        ],
        'supply_t1_setpoint': [
            'Supply T1 Setpoint',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/supply_t1_setpoint'
        ],
        'supply_t1': [
            'Supply T1',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/supply_t1'
        ],
        'hotwater_t2': [
            'Hotwater T2',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/hotWater_t2'
        ],
        'return': [
            'Return',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/return'
        ],
        'switch': [
            'Switch',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/switch'
        ],
        'chimney': [
            'Chimney',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/system/sensors/temperatures/chimney'
        ],
         'hotwater_current_temperature': [
            'Hotwater Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/dhwCircuits/dhw1/actualTemp'
        ],
         'hotwater_current_setpoint': [
            'Hotwater Current Setpoint',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/dhwCircuits/dhw1/currentSetpoint'
        ],
        'hotwater_waterflow': [
            'Hotwater Flow',
            "",
            'mdi:thermometer',
            '/dhwCircuits/dhw1/waterFlow'
        ],
        'hotwater_status': [
            'Hotwater Status',
            "",
            'mdi:thermometer',
            '/dhwCircuits/dhw1/status'
        ],
        'hotwater_operation_mode': [
            'Hotwater Operation Mode',
            "",
            'mdi:thermometer',
            '/dhwCircuits/dhw1/operationMode'
        ],
        'hotwater_charge': [
            'Hotwater Charge',
            "",
            'mdi:thermometer',
            '/dhwCircuits/dhw1/charge'
        ],
        'hotwater_charge_duration': [
            'Hotwater Charge Duration',
            "",
            'mdi:thermometer',
            '/dhwCircuits/dhw1/chargeDuration'
        ],
        'hc1_current_room_setpoint': [
            'HC1 Current Room Setpoint',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc1/currentRoomSetpoint'
        ],
        'hc1_actual_supply_temperature': [
            'HC1 Actual Supply Temp',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc1/actualSupplyTemperature'
        ],
        'hc1_status': [
            'HC1 Status',
            "",
            'mdi:thermometer',
            '/heatingCircuits/hc1/status'
        ],
        'hc1_pump_modulation': [
            'HC1 Pump Modulation',
            "%",
            'mdi:thermometer',
            '/heatingCircuits/hc1/pumpModulation'
        ],
        'hc1_room_temperature': [
            'HC1 Room Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc1/roomtemperature'
        ],
        'hc2_current_room_setpoint': [
            'HC2 Current Room Setpoint',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc2/currentRoomSetpoint'
        ],
        'hc2_actual_supply_temperature': [
            'HC2 Actual Supply Temp',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc2/actualSupplyTemperature'
        ],
        'hc2_status': [
            'HC2 Status',
            "",
            'mdi:thermometer',
            '/heatingCircuits/hc2/status'
        ],
        'hc2_pump_modulation': [
            'HC2 Pump Modulation',
            "%",
            'mdi:thermometer',
            '/heatingCircuits/hc2/pumpModulation'
        ],
        'hc2_room_temperature': [
            'HC2 Room Temperature',
            TEMP_CELSIUS,
            'mdi:thermometer',
            '/heatingCircuits/hc2/roomtemperature'
        ],
        'hs1_actual_modulation': [
            'HS1 Actual Modulation',
            "%",
            'mdi:thermometer',
            '/system/heatSources/hs1/actualModulation'
        ],
        'hs1_actual_power': [
            'HS1 Actual Power',
            "kW",
            'mdi:oil-temperature',
            '/system/heatSources/hs1/actualPower'
        ],
        'hs1_flame_status': [
            'HS1 Flame Status',
            "",
            'mdi:fire',
            '/heatSources/hs1/flameStatus'
        ],
        'hs1_number_of_starts': [
            'HS1 Number of Starts',
            "",
            'mdi:thermometer',
            '/heatSources/hs1/numberOfStarts'
        ],
        'hs1_fuel_density': [
            'HS1 Fuel Density',
            "kg/m3",
            'mdi:thermometer',
            '/heatSources/hs1/fuel/density'
        ],
        'hs1_caloric_value': [
            'HS1 Caloric Value',
            "cal/cm3",
            'mdi:thermometer',
            '/heatSources/hs1/fuel/caloricValue'
        ],
        'hs1_actual_ch_power': [
            'HS1 CH Power',
            "kW",
            'mdi:thermometer',
            '/heatSources/actualCHPower'
        ],
        'hs1_actual_dwh_power': [
            'HS1 DHW Power',
            "kW",
            'mdi:thermometer',
            '/heatSources/actualDHWPower'
        ],


    }

    bridge = hass.data[DOMAIN]

    sensors = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type not in SENSOR_TYPES:
            _LOGGER.warning("Sensor type: %s is not a valid sensor.",
                            sensor_type)
            continue

        sensors.append(
            BuderusSensor(
                hass,
                name="%s %s" % (bridge.name, SENSOR_TYPES[sensor_type][0]),
                bridge=bridge,
                sensor_type=sensor_type,
                unit=SENSOR_TYPES[sensor_type][1],
                icon=SENSOR_TYPES[sensor_type][2],
                km_id=SENSOR_TYPES[sensor_type][3]
            )
        )

    add_devices(sensors, True)


class BuderusSensor(Entity):
    """Representation of a Buderus sensor."""

    def __init__(self, hass, name, bridge: BuderusBridge, sensor_type, unit, icon, km_id):
        """Initialize the Buderus sensor."""
        self._name = name
        self._bridge = bridge
        self._sensor_type = sensor_type
        self._unit = unit
        self._icon = icon
        self._km_id = km_id
        self._state = None

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant."""
        _LOGGER.info("Buderus fetching data...")
        plain = self._bridge._get_data(self._km_id)
        if plain is not None:
            data = self._bridge._get_json(plain)
            self._state = self._bridge._get_value(data)
        _LOGGER.info("Buderus fetching data done.")