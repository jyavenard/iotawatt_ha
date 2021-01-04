"""Support for IoTaWatt Energy monitor."""
from datetime import timedelta
from functools import partial
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import IotaWattEntity, IotawattUpdater
from .const import (
    COORDINATOR,
    DOMAIN,
    SIGNAL_ADD_DEVICE,
    SIGNAL_DELETE_DEVICE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    entities = []

    for idx, ent in enumerate(coordinator.data["sensors"]):
        entity = IotaWattSensor(
            coordinator=coordinator,
            entity=ent,
            mac_address=coordinator.data["sensors"][ent].hub_mac_address,
            name=coordinator.data["sensors"][ent].getName(),
        )
        entities.append(entity)

    async_add_entities(entities)

    async def async_new_entities(sensor_info):
        """Remove an entity."""
        ent = sensor_info["entity"]
        hub_mac_address = sensor_info["mac_address"]
        name = sensor_info["name"]

        entity = IotaWattSensor(
            coordinator=coordinator,
            entity=ent,
            mac_address=hub_mac_address,
            name=name,
        )
        entities=[entity]
        async_add_entities(entities)

    async def async_delete_entities(sensor_info):
        """Remove an entity."""
        sensor_info = "sensor.iotawatt_" + sensor_info
        entity_id = sensor_info.lower()

        platform = "sensor"
        _LOGGER.debug("Sensors: %s", coordinator.data["sensors"])
        #unique_id = coordinator.data["sensors"][sensor_info].getSensorID()

        entity_reg = await hass.helpers.entity_registry.async_get_registry()
        _LOGGER.debug("ID: %s", entity_id)
        entity_check = entity_reg.async_is_registered(entity_id)
        _LOGGER.debug("Ent: %s", entity_id)
        if entity_check:
            _LOGGER.debug("Removing entity: %s", entity_id)
            entity_reg.async_remove(entity_id)

    async_dispatcher_connect(hass, SIGNAL_ADD_DEVICE, async_new_entities)
    async_dispatcher_connect(hass, SIGNAL_DELETE_DEVICE, async_delete_entities)


class IotaWattSensor(IotaWattEntity):
    """Defines a IoTaWatt Energy Sensor."""

    def __init__(self, coordinator, entity, mac_address, name):
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, entity=entity, mac_address=mac_address, name=name)

        self._ent = entity
        self._name = name
        self._io_type = self.coordinator.data["sensors"][self._ent].getType()
        self._state = None

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        if self._io_type == "Input":
            channel = self.coordinator.data["sensors"][self._ent].getChannel()
        else:
            channel = "N/A"

        return {"Type": self._io_type, "Channel": channel}

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self.coordinator.data["sensors"][self._ent].getUnit()

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["sensors"][self._ent].getValue()

    @property
    def name(self):
        """Return the name of the sensor."""
        name = (
            "IoTaWatt "
            + str(self._io_type)
            + " "
            + str(self.coordinator.data["sensors"][self._ent].getName())
        )
        return name

    @property
    def unique_id(self) -> str:
        """Return the Uniqie ID for the sensor."""
        return self.coordinator.data["sensors"][self._ent].getSensorID()
