"""Config flow for CalDAV Filter Calendar."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    IconSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_CALDAV_URL,
    CONF_DESC_KEYWORD,
    CONF_DISCOVERED_CALENDARS,
    CONF_FILTER_CALENDAR,
    CONF_FILTER_ICON,
    CONF_FILTER_ID,
    CONF_FILTER_NAME,
    CONF_FILTERS,
    CONF_PASSWORD,
    CONF_POLL_INTERVAL,
    CONF_TITLE_KEYWORD,
    CONF_USERNAME,
    DEFAULT_FILTER_ICON,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _test_connection(url: str, username: str, password: str) -> list[str]:
    """Connect to CalDAV server and return list of calendar names."""
    import caldav  # noqa: PLC0415

    client = caldav.DAVClient(url=url, username=username, password=password)
    principal = client.principal()
    return [cal.name for cal in principal.calendars() if cal.name]


class CalDAVFilterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CalDAV Filter Calendar."""

    VERSION = 2

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._discovered_calendars: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_CALDAV_URL].rstrip("/")
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            self._async_abort_entries_match(
                {CONF_CALDAV_URL: url, CONF_USERNAME: username}
            )

            try:
                self._discovered_calendars = await self.hass.async_add_executor_job(
                    _test_connection, url, username, password
                )
            except Exception as err:
                import caldav  # noqa: PLC0415
                import requests  # noqa: PLC0415

                if isinstance(err, caldav.lib.error.AuthorizationError):
                    errors["base"] = "invalid_auth"
                elif isinstance(err, requests.exceptions.ConnectionError):
                    errors["base"] = "cannot_connect"
                else:
                    _LOGGER.exception("Unexpected error during CalDAV connection test")
                    errors["base"] = "unknown"
            else:
                if not self._discovered_calendars:
                    errors["base"] = "no_calendars"
                else:
                    self._data = {
                        CONF_CALDAV_URL: url,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_POLL_INTERVAL: user_input.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                        ),
                        CONF_DISCOVERED_CALENDARS: self._discovered_calendars,
                    }
                    return await self.async_step_add_filter()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CALDAV_URL): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): vol.All(int, vol.Range(min=1, max=1440)),
                }
            ),
            errors=errors,
        )

    async def async_step_add_filter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            new_filter = {
                CONF_FILTER_ID: str(uuid.uuid4()),
                CONF_FILTER_NAME: user_input[CONF_FILTER_NAME],
                CONF_FILTER_CALENDAR: user_input[CONF_FILTER_CALENDAR],
                CONF_FILTER_ICON: user_input.get(CONF_FILTER_ICON, DEFAULT_FILTER_ICON),
                CONF_TITLE_KEYWORD: user_input.get(CONF_TITLE_KEYWORD, ""),
                CONF_DESC_KEYWORD: user_input.get(CONF_DESC_KEYWORD, ""),
            }
            return self.async_create_entry(
                title=f"CalDAV: {self._data[CONF_USERNAME]}",
                data=self._data,
                options={CONF_FILTERS: [new_filter]},
            )

        cal_options = [
            {"value": c, "label": c} for c in self._discovered_calendars
        ]
        return self.async_show_form(
            step_id="add_filter",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FILTER_NAME): str,
                    vol.Required(CONF_FILTER_CALENDAR): SelectSelector(
                        SelectSelectorConfig(
                            options=cal_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_FILTER_ICON, default=DEFAULT_FILTER_ICON): IconSelector(),
                    vol.Optional(CONF_TITLE_KEYWORD, default=""): str,
                    vol.Optional(CONF_DESC_KEYWORD, default=""): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> CalDAVFilterOptionsFlow:
        return CalDAVFilterOptionsFlow()


# ---------------------------------------------------------------------------
# Options Flow
# ---------------------------------------------------------------------------

class CalDAVFilterOptionsFlow(OptionsFlow):
    """Manage filters for an existing CalDAV connection."""

    def __init__(self) -> None:
        self._filters: list[dict[str, Any]] = []
        self._discovered_calendars: list[str] = []
        self._edit_filter_id: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        self._filters = list(self.config_entry.options.get(CONF_FILTERS, []))
        self._discovered_calendars = self.config_entry.data.get(
            CONF_DISCOVERED_CALENDARS, []
        )

        menu_options = (
            ["add_filter", "edit_filter", "delete_filter", "connection"]
            if self._filters
            else ["add_filter", "connection"]
        )
        return self.async_show_menu(step_id="init", menu_options=menu_options)

    # --- Add filter ---

    async def async_step_add_filter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._filters.append(
                {
                    CONF_FILTER_ID: str(uuid.uuid4()),
                    CONF_FILTER_NAME: user_input[CONF_FILTER_NAME],
                    CONF_FILTER_CALENDAR: user_input[CONF_FILTER_CALENDAR],
                    CONF_FILTER_ICON: user_input.get(CONF_FILTER_ICON, DEFAULT_FILTER_ICON),
                    CONF_TITLE_KEYWORD: user_input.get(CONF_TITLE_KEYWORD, ""),
                    CONF_DESC_KEYWORD: user_input.get(CONF_DESC_KEYWORD, ""),
                }
            )
            return self._save()

        cal_options = [{"value": c, "label": c} for c in self._discovered_calendars]
        return self.async_show_form(
            step_id="add_filter",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FILTER_NAME): str,
                    vol.Required(CONF_FILTER_CALENDAR): SelectSelector(
                        SelectSelectorConfig(
                            options=cal_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_FILTER_ICON, default=DEFAULT_FILTER_ICON): IconSelector(),
                    vol.Optional(CONF_TITLE_KEYWORD, default=""): str,
                    vol.Optional(CONF_DESC_KEYWORD, default=""): str,
                }
            ),
        )

    # --- Edit filter (step 1: select which one) ---

    async def async_step_edit_filter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._edit_filter_id = user_input[CONF_FILTER_ID]
            return await self.async_step_edit_filter_form()

        filter_options = [
            {"value": f[CONF_FILTER_ID], "label": f[CONF_FILTER_NAME]}
            for f in self._filters
        ]
        return self.async_show_form(
            step_id="edit_filter",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FILTER_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=filter_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    # --- Edit filter (step 2: edit form) ---

    async def async_step_edit_filter_form(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = next(
            (f for f in self._filters if f[CONF_FILTER_ID] == self._edit_filter_id),
            {},
        )

        if user_input is not None:
            self._filters = [
                {
                    CONF_FILTER_ID: self._edit_filter_id,
                    CONF_FILTER_NAME: user_input[CONF_FILTER_NAME],
                    CONF_FILTER_CALENDAR: user_input[CONF_FILTER_CALENDAR],
                    CONF_FILTER_ICON: user_input.get(CONF_FILTER_ICON, DEFAULT_FILTER_ICON),
                    CONF_TITLE_KEYWORD: user_input.get(CONF_TITLE_KEYWORD, ""),
                    CONF_DESC_KEYWORD: user_input.get(CONF_DESC_KEYWORD, ""),
                }
                if f[CONF_FILTER_ID] == self._edit_filter_id
                else f
                for f in self._filters
            ]
            return self._save()

        cal_options = [{"value": c, "label": c} for c in self._discovered_calendars]
        return self.async_show_form(
            step_id="edit_filter_form",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FILTER_NAME,
                        default=current.get(CONF_FILTER_NAME, ""),
                    ): str,
                    vol.Required(
                        CONF_FILTER_CALENDAR,
                        default=current.get(CONF_FILTER_CALENDAR),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=cal_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_FILTER_ICON,
                        default=current.get(CONF_FILTER_ICON, DEFAULT_FILTER_ICON),
                    ): IconSelector(),
                    vol.Optional(
                        CONF_TITLE_KEYWORD,
                        default=current.get(CONF_TITLE_KEYWORD, ""),
                    ): str,
                    vol.Optional(
                        CONF_DESC_KEYWORD,
                        default=current.get(CONF_DESC_KEYWORD, ""),
                    ): str,
                }
            ),
        )

    # --- Delete filter ---

    async def async_step_delete_filter(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            delete_id = user_input[CONF_FILTER_ID]
            self._filters = [
                f for f in self._filters if f[CONF_FILTER_ID] != delete_id
            ]
            return self._save()

        filter_options = [
            {"value": f[CONF_FILTER_ID], "label": f[CONF_FILTER_NAME]}
            for f in self._filters
        ]
        return self.async_show_form(
            step_id="delete_filter",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FILTER_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=filter_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    # --- Connection settings ---

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            # Update poll_interval in entry data requires a data update
            # We store it in options so coordinator picks it up on reload
            options = dict(self.config_entry.options)
            options[CONF_POLL_INTERVAL] = user_input[CONF_POLL_INTERVAL]
            options[CONF_FILTERS] = self._filters
            return self.async_create_entry(title="", data=options)

        current_interval = self.config_entry.options.get(
            CONF_POLL_INTERVAL,
            self.config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        )
        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL, default=current_interval
                    ): vol.All(int, vol.Range(min=1, max=1440)),
                }
            ),
        )

    def _save(self) -> FlowResult:
        options = dict(self.config_entry.options)
        options[CONF_FILTERS] = self._filters
        return self.async_create_entry(title="", data=options)
