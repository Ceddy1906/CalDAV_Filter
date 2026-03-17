"""Calendar platform for CalDAV Filter Calendar."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DESC_KEYWORD,
    CONF_FILTER_CALENDAR,
    CONF_FILTER_ICON,
    CONF_FILTER_ID,
    CONF_FILTER_NAME,
    CONF_TITLE_KEYWORD,
    DEFAULT_FILTER_ICON,
    DOMAIN,
)
from .coordinator import CalDAVFilterCoordinator, get_filters

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one CalendarEntity per filter configuration."""
    coordinator: CalDAVFilterCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            CalDAVFilterCalendarEntity(coordinator, config_entry, f)
            for f in get_filters(config_entry)
        ],
        update_before_add=True,
    )


class CalDAVFilterCalendarEntity(
    CoordinatorEntity[CalDAVFilterCoordinator], CalendarEntity
):
    """A single filtered calendar entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CalDAVFilterCoordinator,
        config_entry: ConfigEntry,
        filter_cfg: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._filter_id: str = filter_cfg[CONF_FILTER_ID]
        self._attr_unique_id = f"{config_entry.entry_id}_{self._filter_id}"
        self._attr_name = filter_cfg[CONF_FILTER_NAME]
        self._attr_icon = filter_cfg.get(CONF_FILTER_ICON, DEFAULT_FILTER_ICON)

    def _current_filter(self) -> dict[str, Any]:
        """Return the up-to-date filter config from the entry."""
        for f in get_filters(self._config_entry):
            if f[CONF_FILTER_ID] == self._filter_id:
                return f
        return {}

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming filtered event."""
        now = dt_util.now()
        for evt in sorted(self._get_filtered_events(), key=lambda e: e.start):
            if evt.end > now:
                return evt
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[CalendarEvent]:
        """Return filtered events within the requested time range."""
        return [
            evt
            for evt in self._get_filtered_events()
            if evt.end >= start_datetime and evt.start <= end_datetime
        ]

    def _get_filtered_events(self) -> list[CalendarEvent]:
        """Apply filter keywords to the coordinator's calendar data."""
        if not self.coordinator.data:
            return []

        cfg = self._current_filter()
        cal_name: str = cfg.get(CONF_FILTER_CALENDAR, "")
        raw: list[CalendarEvent] = self.coordinator.data.get(cal_name, [])

        title_kw = (cfg.get(CONF_TITLE_KEYWORD) or "").strip().lower()
        desc_kw = (cfg.get(CONF_DESC_KEYWORD) or "").strip().lower()

        return [
            evt
            for evt in raw
            if (not title_kw or title_kw in (evt.summary or "").lower())
            and (not desc_kw or desc_kw in (evt.description or "").lower())
        ]
