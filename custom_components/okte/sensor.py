"""Sensor platform for the OKTE DAM integration."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OkteDamCoordinator

# EUR/MWh is not a built-in HA unit constant — use a plain string.
UNIT_EUR_MWH = "EUR/MWh"


@dataclass(frozen=True, kw_only=True)
class OkteSensorEntityDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with the coordinator data key."""

    coordinator_key: str = ""


SENSOR_DESCRIPTIONS: tuple[OkteSensorEntityDescription, ...] = (
    OkteSensorEntityDescription(
        key="prices",
        coordinator_key="current_price",
        name="Prices",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:currency-eur",
    ),
    OkteSensorEntityDescription(
        key="current_period",
        coordinator_key="current_period",
        name="Current Period",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ),
    OkteSensorEntityDescription(
        key="today_min",
        coordinator_key="today_min",
        name="Today Min Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold",
    ),
    OkteSensorEntityDescription(
        key="today_max",
        coordinator_key="today_max",
        name="Today Max Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold",
    ),
    OkteSensorEntityDescription(
        key="today_avg",
        coordinator_key="today_avg",
        name="Today Avg Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:approximately-equal",
    ),
    OkteSensorEntityDescription(
        key="tomorrow_min",
        coordinator_key="tomorrow_min",
        name="Tomorrow Min Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold",
    ),
    OkteSensorEntityDescription(
        key="tomorrow_max",
        coordinator_key="tomorrow_max",
        name="Tomorrow Max Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold",
    ),
    OkteSensorEntityDescription(
        key="tomorrow_avg",
        coordinator_key="tomorrow_avg",
        name="Tomorrow Avg Price",
        native_unit_of_measurement=UNIT_EUR_MWH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:approximately-equal",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OKTE DAM sensors from a config entry."""
    coordinator: OkteDamCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OkteDamSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class OkteDamSensor(CoordinatorEntity[OkteDamCoordinator], SensorEntity):
    """Representation of an OKTE DAM sensor."""

    entity_description: OkteSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OkteDamCoordinator,
        description: OkteSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="OKTE",
            model="Day-Ahead Market",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value from coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.coordinator_key)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Expose price schedules on the current_price sensor."""
        if self.entity_description.key != "prices" or self.coordinator.data is None:
            return None
        return {
            "prices": self.coordinator.data.get("prices", []),
        }
