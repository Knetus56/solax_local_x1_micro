# SolaX Local X1 Micro - Home Assistant Integration

[![CI](https://github.com/Knetus56/solax_local_x1_micro/actions/workflows/ci.yml/badge.svg)](https://github.com/Knetus56/solax_local_x1_micro/actions/workflows/ci.yml)

A [Home Assistant](https://www.home-assistant.io/) integration to control and monitor your **SolaX** inverter locally over HTTP.

## 🌟 Features

- 📊 **Real-time monitoring**: MPPT power, energy production, temperature
- 🔄 **Inverter control**: turn on/off via a switch
- 📈 **Production tracking**: daily and cumulative production
- 🕐 **History**: last-update timestamp
- 🌍 **Multi-inverter support**: X1 Micro 2-in-1
- 🔐 **Local connection**: no cloud, fully local
- 🇫🇷 **Localized UI**: French, English and Dutch (entities fully translated according to Home Assistant's language)
- ⚙️ **Editable afterwards**: change the IP address or the poll interval without recreating the integration
- 🌙 **Automatic night pause**: no unnecessary requests overnight (based on sunset/sunrise, 1h margin)

## 📋 Sensors

| Sensor | Description | Unit |
|---------|-------------|-------|
| `mppt1_puissance` | MPPT 1 power | W |
| `mppt1_voltage` | MPPT 1 voltage | V |
| `mppt1_intensite` | MPPT 1 current | A |
| `mppt2_puissance` | MPPT 2 power | W |
| `mppt2_voltage` | MPPT 2 voltage | V |
| `mppt2_intensite` | MPPT 2 current | A |
| `inverter_voltage` | Inverter output voltage | V |
| `inverter_intensite` | Inverter output current | A |
| `inverter_puissance` | Inverter output power | W |
| `inverter_freq` | Inverter frequency | Hz |
| `temp` | Inverter temperature | °C |
| `prod_auj` | Today's production | kWh |
| `prod_total` | Cumulative total production | kWh |
| `mode` | Operating mode | WaitMode/CheckMode/NormalMode |
| `ip` | Inverter IP address | - |
| `num_inverter` | Serial number | - |
| `last_update` | Last update | timestamp |

## 🔌 Control Entities

- **Binary Sensor**: online/offline status
- **Switch**: turn the inverter on/off
- **Number**: production ratio (0-100%) - read directly from the inverter at Home Assistant startup, on every inverter reconnection, and after every change

## 🔄 Services

### Refresh all inverters

Service: `solax_local.refresh_all`

Forces an immediate update of all configured inverters without waiting for the poll interval.

**Usage in an automation**:
```yaml
service: solax_local.refresh_all
```

**Or from Developer Tools**:
1. **Developer Tools** > **Services**
2. Select `SolaX Local X1 Micro: Refresh all inverters`
3. Click **Run**

## 🚀 Installation

### Requirements

- Home Assistant 2023.12+
- Network access to the SolaX inverter
- The inverter's IP address and serial number

### Via HACS (recommended)

**Once the integration is accepted into the official HACS store**:
1. Open Home Assistant
2. Go to **HACS** > **Integrations** > **Explore & download**
3. Search for "SolaX Local X1 Micro"
4. Click **Download**
5. Restart Home Assistant

**In the meantime** (or to follow a specific branch/version), add it as a custom repository:

**Direct HACS link**:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Knetus56&repository=solax_local_x1_micro&category=integration)

Or manually:
1. Open Home Assistant
2. Go to **HACS** > **Integrations**
3. Click the **menu** (⋯) > **Custom repositories**
4. Add the URL: `https://github.com/Knetus56/solax_local_x1_micro`
5. Search for "SolaX Local X1 Micro"
6. Click **Install**
7. Restart Home Assistant

### Manual installation

1. Download the latest [release](https://github.com/Knetus56/solax_local_x1_micro/releases)
2. Extract into `custom_components/solax_local/`
3. Restart Home Assistant

## ⚙️ Configuration

### Via the Home Assistant UI

1. **Settings** > **Devices & services** > **Integrations**
2. Click **Add integration**
3. Search for and select **SolaX Local X1 Micro**
4. Fill in the details:
   - **IP**: the inverter's IP address (e.g. `192.168.1.100`)
   - **Inverter type**: select the model
   - **Serial number**: the inverter's serial number
   - **Poll interval** (optional): update frequency in seconds (default: 300s)

> The serial number is automatically normalized to uppercase.

### Changing the configuration after installation

You no longer need to remove/recreate the integration to change the IP address or the poll interval:

1. **Settings** > **Devices & services**
2. Find the **SolaX Local X1 Micro** card > click **Configure** (⚙️ icon)
3. Update the **host** and/or the **poll interval**
4. Submit — the integration reloads automatically with the new values

The inverter type and serial number stay fixed after creation (they identify the device); recreate the integration to change them.

## 🔧 Advanced configuration

### Update interval

By default, the integration polls the inverter every **300 seconds** (5 minutes). You can adjust it during setup.

### Night pause (based on `sun.sun`)

SolaX inverters turn off their Wi-Fi dongle at night: any request sent during that time fails anyway (timeout). The integration avoids these useless calls by relying on the **`sun.sun`** entity, built into Home Assistant natively (the `sun` component, almost always present — it computes the actual sunrise/sunset based on the geographic position and time zone configured in **Settings > System > General**).

**How it works**: on every poll cycle, the integration checks whether the sun has been down for more than 1h *and* will stay down for at least 1h more. Only then — a night "settled in", far from any transition — is the HTTP request skipped outright. This double check (1h before *and* 1h after the current instant) naturally creates a symmetric **1-hour** margin around the actual sunset and sunrise, without having to compute the astronomical times itself:

```
                      actual sunset                        actual sunrise
                            │                                      │
   ── normal requests ──────┤── 1h margin ──┤ PAUSE (no request) ├── 1h margin ──┤── normal requests ──
                                            │                       │
                                     sunset + 1h              sunrise - 1h
```

Concretely: if the sun sets at 8:00 PM, the integration keeps polling the inverter until 9:00 PM, then pauses. If sunrise is at 7:00 AM the next day, it resumes at 6:00 AM — so as not to miss an inverter that starts up a bit earlier or later than expected (clouds, season, the inverter's internal clock drifting, etc.).

**If the `sun.sun` entity doesn't exist** (Sun component disabled or manually removed): the night pause disables itself automatically and silently — the integration polls normally on **every** cycle, day and night, exactly as before this feature was added. No configuration is needed for this case, and no error is raised.

**Effect on sensors during the pause**: same as a regular network error — instantaneous readings (power, voltage, current, frequency, temperature) go to `0`, `mode` shows "Unknown", `prod_auj`/`prod_total` keep their last known value (see next section). The `binary_sensor.online` sensor turns `Off`.

This pause isn't configurable yet (no on/off toggle or margin setting in the UI) — open an issue on the repo if you need one.

### DIAGNOSTIC entities

The following entities are hidden by default (Advanced tab):
- Mode status
- IP address
- Serial number
- Last update

To show them: **Settings** > **Devices & services** > select the device > **Show disabled/hidden entities**


### Sensors show "Unknown"

- Normal at night (automatic night pause, see above) or after a one-off request error — `mode` goes back to "Unknown" until the next successful poll
- Check that the IP address is correct
- Check that the inverter is **online** and **powered**
- Check the **network connectivity** between HA and the inverter
- Increase the `poll interval` if you're seeing network timeouts

### The integration doesn't load

- Check the logs: **Settings** > **System** > **Logs**
- Look for connection errors
- Restart Home Assistant

### The device doesn't show the model

- This means the selected model isn't recognized
- Double-check the selection made during setup


## 📦 Versions

- **v1.4.7** (2026-09-21) - New `number` entity to control the inverter's production ratio (0-100%) locally, without the SolaX app. Writing (`build_set_ratio_packet`) comes from the official app's JS; reading (`build_get_ratio_packet`) had no available documentation and was reverse-engineered empirically instead, by comparing responses before/after a known write to locate the register offset. Since the inverter doesn't expose this setting in its regular telemetry, the displayed value is confirmed with a real read at Home Assistant startup, on every inverter reconnection (morning restart after the overnight Wi-Fi shutdown), and 2s after every manual change; it resets to "unknown" at midnight so it never shows an unverified value overnight.


## 🙏 Credits

- https://github.com/CurlyMoo for the reverse-engineering work here: https://github.com/squishykid/solax/issues/191
