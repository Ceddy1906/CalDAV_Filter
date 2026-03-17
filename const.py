"""Constants for the CalDAV Filter Calendar integration."""

DOMAIN = "caldav_filter"

# Connection config (stored in entry.data)
CONF_CALDAV_URL = "url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_POLL_INTERVAL = "poll_interval"
CONF_DISCOVERED_CALENDARS = "discovered_calendars"

# Filter list (stored in entry.options)
CONF_FILTERS = "filters"
CONF_FILTER_ID = "filter_id"
CONF_FILTER_NAME = "filter_name"
CONF_FILTER_CALENDAR = "filter_calendar"
CONF_FILTER_ICON = "filter_icon"

DEFAULT_FILTER_ICON = "mdi:calendar"
CONF_TITLE_KEYWORD = "title_keyword"
CONF_DESC_KEYWORD = "desc_keyword"

# Defaults
DEFAULT_POLL_INTERVAL = 15  # minutes
LOOKAHEAD_DAYS = 60

PLATFORMS = ["calendar"]
