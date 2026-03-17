"""DataUpdateCoordinator for CalDAV Filter Calendar."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CALDAV_URL,
    CONF_FILTER_CALENDAR,
    CONF_FILTERS,
    CONF_PASSWORD,
    CONF_POLL_INTERVAL,
    CONF_USERNAME,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    LOOKAHEAD_DAYS,
)

_LOGGER = logging.getLogger(__name__)


def get_filters(config_entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return the current filter list, options take priority over data."""
    return config_entry.options.get(
        CONF_FILTERS,
        config_entry.data.get(CONF_FILTERS, []),
    )


class CalDAVFilterCoordinator(DataUpdateCoordinator[dict[str, list[CalendarEvent]]]):
    """Polls CalDAV server and returns events grouped by calendar name."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        poll_interval = int(
            config_entry.options.get(
                CONF_POLL_INTERVAL,
                config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
            )
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=poll_interval),
        )
        self.config_entry = config_entry

    def _calendars_to_fetch(self) -> set[str]:
        """Derive the set of calendar names needed by the current filters."""
        return {
            f[CONF_FILTER_CALENDAR]
            for f in get_filters(self.config_entry)
            if CONF_FILTER_CALENDAR in f
        }

    async def _async_update_data(self) -> dict[str, list[CalendarEvent]]:
        try:
            return await self.hass.async_add_executor_job(self._fetch_events)
        except Exception as err:
            import caldav  # noqa: PLC0415
            import requests  # noqa: PLC0415

            if isinstance(err, caldav.lib.error.AuthorizationError):
                raise UpdateFailed(f"Authentication error: {err}") from err
            if isinstance(err, requests.exceptions.ConnectionError):
                raise UpdateFailed(f"Cannot connect to CalDAV server: {err}") from err
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _fetch_events(self) -> dict[str, list[CalendarEvent]]:
        """Synchronous – runs in executor thread."""
        import caldav  # noqa: PLC0415

        client = caldav.DAVClient(
            url=self.config_entry.data[CONF_CALDAV_URL],
            username=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
        )
        principal = client.principal()

        now = dt_util.now()
        end = now + timedelta(days=LOOKAHEAD_DAYS)
        needed = self._calendars_to_fetch()
        result: dict[str, list[CalendarEvent]] = {}

        for calendar in principal.calendars():
            cal_name = calendar.name
            if cal_name not in needed:
                continue

            try:
                raw_events = calendar.date_search(start=now, end=end, expand=True)
            except Exception as err:
                _LOGGER.warning("Error fetching calendar %s: %s", cal_name, err)
                result[cal_name] = []
                continue

            parsed: list[CalendarEvent] = []
            for raw in raw_events:
                try:
                    evt = _parse_event(raw, now)
                    if evt is not None:
                        parsed.append(evt)
                except Exception as err:
                    _LOGGER.debug("Skipping unparseable event: %s", err)

            result[cal_name] = parsed

        return result


def _parse_event(caldav_event: Any, now: datetime) -> CalendarEvent | None:
    """Convert a caldav Event to a HA CalendarEvent dataclass."""
    try:
        comp = caldav_event.vobject_instance.vevent
    except Exception:
        return None

    dtstart_raw = comp.dtstart.value
    dtstart = _to_datetime(dtstart_raw)
    if dtstart is None:
        return None

    if hasattr(comp, "dtend"):
        dtend = _to_datetime(comp.dtend.value) or dtstart
    elif hasattr(comp, "duration"):
        dtend = dtstart + comp.duration.value
    else:
        dtend = dtstart

    # Skip unexpanded recurring master events (RRULE present, both times in the past)
    if hasattr(comp, "rrule") and dtstart < now and dtend < now:
        return None

    summary = str(comp.summary.value) if hasattr(comp, "summary") else ""
    description = str(comp.description.value) if hasattr(comp, "description") else ""
    uid = str(comp.uid.value) if hasattr(comp, "uid") else None

    return CalendarEvent(
        summary=summary,
        start=dtstart,
        end=dtend,
        description=description,
        uid=uid,
    )


def _to_datetime(value: datetime | date) -> datetime | None:
    """Normalize a date or datetime to a UTC-aware datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return dt_util.as_utc(
                value.replace(tzinfo=dt_util.get_default_time_zone())
            )
        return dt_util.as_utc(value)
    if isinstance(value, date):
        local_tz = dt_util.get_default_time_zone()
        return dt_util.as_utc(
            datetime(value.year, value.month, value.day, tzinfo=local_tz)
        )
    return None
