"""DataUpdateCoordinator for the OKTE DAM integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class OkteDamCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that fetches DAM results from the OKTE API."""

    def __init__(self, hass, session: aiohttp.ClientSession) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self._session = session

    async def _async_update_data(self) -> dict:
        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)
        params = {
            "deliveryDayFrom": today.isoformat(),
            "deliveryDayTo": tomorrow.isoformat(),
        }
        try:
            async with self._session.get(API_URL, params=params) as resp:
                if resp.status != 200:
                    raise UpdateFailed(
                        f"OKTE API returned HTTP {resp.status}"
                    )
                entries = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with OKTE API: {err}") from err

        return _parse(entries)


def _parse(entries: list[dict]) -> dict:
    """Parse raw API entries into the 8 sensor values."""
    now = datetime.now(timezone.utc)

    today_str = now.date().isoformat()
    tomorrow_str = (now.date() + timedelta(days=1)).isoformat()

    today_prices: list[float] = []
    tomorrow_prices: list[float] = []
    schedule: list[dict] = []
    current_price: float | None = None
    current_period: int | None = None

    for entry in entries:
        try:
            price = float(entry["price"])
            delivery_day = entry.get("deliveryDay", "")
            start_raw = entry.get("deliveryStart", "")
            end_raw = entry.get("deliveryEnd", "")
            period = int(entry["period"])

            if delivery_day == today_str:
                today_prices.append(price)
            elif delivery_day == tomorrow_str:
                tomorrow_prices.append(price)

            if start_raw and end_raw:
                start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))

                if end > now:
                    schedule.append({"period": period, "start": start_raw, "price": price})
                if start <= now < end:
                    current_price = price
                    current_period = period

        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.debug("Skipping malformed entry %s: %s", entry, err)

    def _safe_min(lst: list[float]) -> float | None:
        return min(lst) if lst else None

    def _safe_max(lst: list[float]) -> float | None:
        return max(lst) if lst else None

    def _safe_avg(lst: list[float]) -> float | None:
        return round(sum(lst) / len(lst), 4) if lst else None

    return {
        "current_price": current_price,
        "current_period": current_period,
        "prices": sorted(schedule, key=lambda x: x["start"]),
        "today_min": _safe_min(today_prices),
        "today_max": _safe_max(today_prices),
        "today_avg": _safe_avg(today_prices),
        "tomorrow_min": _safe_min(tomorrow_prices),
        "tomorrow_max": _safe_max(tomorrow_prices),
        "tomorrow_avg": _safe_avg(tomorrow_prices),
    }
