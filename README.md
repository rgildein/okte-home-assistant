# OKTE DAM — Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

A [HACS](https://hacs.xyz)-compatible Home Assistant custom integration that exposes Slovak [OKTE Day-Ahead Market (DAM)](https://isot.okte.sk) electricity prices as sensor entities.

## Sensors

| Entity | Description |
|--------|-------------|
| `sensor.okte_dam_prices` | Current price (EUR/MWh) — state is `prices[0]`, carries full `prices` attribute |
| `sensor.okte_dam_current_period` | Period number of the current 15-minute slot (1–96) |
| `sensor.okte_dam_min_price` | Minimum price across all fetched periods (EUR/MWh) |
| `sensor.okte_dam_max_price` | Maximum price across all fetched periods (EUR/MWh) |
| `sensor.okte_dam_avg_price` | Average price across all fetched periods (EUR/MWh) |

### Price schedule attributes

The `sensor.okte_dam_current_price` entity exposes a `prices` attribute — a chronologically sorted list of all **upcoming** 15-minute periods (current period onwards, today + tomorrow). Past periods are excluded. The list shrinks as the day progresses and grows again after ~14:00 CET when tomorrow's data is published.

Each entry looks like:
```json
{"period": 68, "start": "2026-02-23T16:45:00Z", "price": 128.65}
```

Example templates:

```yaml
# Current price (= sensor state)
{{ states('sensor.okte_dam_prices') }}

# Next price (prices[1])
{{ state_attr('sensor.okte_dam_prices', 'prices')[1].price }}

# Minimum price in the remaining schedule
{{ state_attr('sensor.okte_dam_prices', 'prices') | map(attribute='price') | min }}

# Find the 4 cheapest upcoming periods for battery charging
{{ state_attr('sensor.okte_dam_prices', 'prices')
   | sort(attribute='price') | map(attribute='start') | list | first(4) }}
```

## Installation via HACS

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → three-dot menu → **Custom repositories**.
3. Add `https://github.com/rgildein/okte-home-assistant` with category **Integration**.
4. Find **OKTE DAM** in the list and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration**, search for **OKTE DAM**, and follow the setup wizard.

## Manual Installation

1. Copy `custom_components/okte/` to your `<config>/custom_components/okte/` directory.
2. Restart Home Assistant.
3. Add the integration via UI as above.

## Data Source

Data is fetched from the public OKTE API:

```
GET https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=YYYY-MM-DD&deliveryDayTo=YYYY-MM-DD
```

No authentication is required. Data is refreshed every **30 minutes**.

## Dashboard Example

See [`dashboard_example.yaml`](dashboard_example.yaml) for a ready-to-use Lovelace configuration featuring:
- **Upcoming price chart** — bar chart of all available periods (today + tomorrow) with color thresholds (green/orange/red), requires [apexcharts-card](https://github.com/RomRider/apexcharts-card) from HACS
- **Min/Avg/Max** — summary cards

Paste its contents into **Edit dashboard → Raw configuration editor**.

> **Prerequisite:** Install [apexcharts-card](https://github.com/RomRider/apexcharts-card) via HACS before using the dashboard.

## Verification

Cross-check the current price manually:

```bash
curl "https://isot.okte.sk/api/v1/dam/results?deliveryDayFrom=$(date +%Y-%m-%d)&deliveryDayTo=$(date +%Y-%m-%d)" | python3 -m json.tool | grep -A5 '"period"'
```

## License

MIT
