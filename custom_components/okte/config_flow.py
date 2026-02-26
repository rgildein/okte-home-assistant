"""Config flow for the OKTE DAM integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("name", default=DEFAULT_NAME): str,
    }
)


class OkteDamConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OKTE DAM."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            error = await self._test_connectivity()
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(
                    title=user_input.get("name", DEFAULT_NAME),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connectivity(self) -> str | None:
        """Return an error key string on failure, or None on success."""
        today = datetime.now(timezone.utc).date().isoformat()
        params = {"deliveryDayFrom": today, "deliveryDayTo": today}
        session = async_get_clientsession(self.hass, verify_ssl=False)
        try:
            async with session.get(API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    _LOGGER.error("OKTE API returned HTTP %s during config flow", resp.status)
                    return "cannot_connect"
        except aiohttp.ClientError as err:
            _LOGGER.error("Cannot reach OKTE API: %s", err)
            return "cannot_connect"
        return None
