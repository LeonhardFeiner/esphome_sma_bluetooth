# ESPHome SMA Bluetooth Component

ESPHome external component for reading data from SMA solar inverters via Bluetooth Classic. Supports **multiple inverters** on a single ESP32 with **autodiscovery** — each inverter appears as a **separate sub-device** in Home Assistant.

Fork maintained with active production features:
- **On-Demand Historical Data HTTP Streaming** directly from inverter flash ring buffers (5-min spot records and daily lifetime yields)
- **Automatic Inverter RTC Synchronization** via SNTP
- **Live Event & Hardware Fault Reporting** (`inverter_fault`, `last_event`, `last_event_code`)
- **Advanced Diagnostics** (`efficiency`, `insulation_resistance`, `inverter_status`)
- **Dynamic Polling & Memory Optimization** for long-term stability with Ethernet (WT32-ETH01) and Bluetooth Classic

---

## Features

- **Multi-inverter support** — connect to 1–10+ SMA inverters sequentially from one ESP32
- **Autodiscovery** — automatically finds SMA inverters via Bluetooth Classic GAP scanning
- **Sub-devices** — each inverter appears as its own device in Home Assistant (requires ESPHome 2025.7.0+)
- **Persistent discovery** — discovered inverter MACs are cached in NVS flash and survive reboots (including overnight when inverters are off)
- **Smart password handling** — configurable default password list, per-inverter overrides, auto-caching of working passwords (with NVS retention protection)
- **Comprehensive sensor suite** — AC/DC power, voltage, current, frequency, energy yields, efficiency, insulation resistance, operating status, and event codes
- **Automatic Inverter RTC Time Sync** — keeps inverter internal clocks synchronized from ESPHome's SNTP time source during logon
- **On-Demand HTTP History Streaming** — download 5-minute spot data and lifetime daily yields as CSV via simple HTTP GET requests without filling ESP32 RAM
- **Dynamic Polling Interval** — automatically slows down polling when inverters enter night standby
- **Zero-config mode** — just add `sma_bluetooth:` and it works

---

## Requirements

- **ESP32 (original only)** — ESP32-S2/S3/C3/C6 do **NOT** support Bluetooth Classic (BR/EDR)
- **ESP-IDF framework** (not Arduino)
- **ESPHome 2025.7.0+** (for sub-device support)
- **Home Assistant 2025.7.0+** (for sub-device display)

---

## Quick Start

### Plug and Play (zero config)

```yaml
external_components:
  - source: github://LeonhardFeiner/esphome_sma_bluetooth@main
    components: [sma_bluetooth]

sma_bluetooth:
```

This will:
1. Scan for all nearby SMA inverters
2. Try default passwords ("0000", "1111")
3. Auto-create all sensors per inverter (named "SMA {MAC} {metric}")
4. Register each inverter as a separate sub-device in Home Assistant
5. Cache discovered MACs to flash so sensors persist across reboots

### With Inverter Config & Advanced Sensors

```yaml
external_components:
  - source: github://LeonhardFeiner/esphome_sma_bluetooth@main
    components: [sma_bluetooth]

sma_bluetooth:
  passwords:
    - "0000"
    - "1111"
  inverters:
    - mac_address: "00:80:25:AA:BB:CC"
      name: "Süd Dach PV 1"
    - mac_address: "00:80:25:DD:EE:FF"
      name: "West Dach PV 2"
      password: "1234"
```

When `inverters` is set, only those MAC addresses are accepted. Per-inverter `password` overrides the default list.

### Manual Mode (Explicit Sensors)

```yaml
sma_bluetooth:
  id: sma_hub
  discovery: false

sensor:
  - platform: sma_bluetooth
    sma_bluetooth_id: sma_hub
    mac_address: "00:80:25:AA:BB:CC"
    password: "0000"
    update_interval: 60s
    dynamic_interval: true
    pv1:
      voltage:
        name: "DC Voltage Strang 1"
      current:
        name: "DC Current Strang 1"
      active_power:
        name: "DC Power Strang 1"
    pv2:
      voltage:
        name: "DC Voltage Strang 2"
      current:
        name: "DC Current Strang 2"
      active_power:
        name: "DC Power Strang 2"
    phase_a:
      voltage:
        name: "AC Voltage L1"
      active_power:
        name: "AC Power L1"
    frequency:
      name: "Grid Frequency"
    efficiency:
      name: "Inverter Efficiency"
    insulation_resistance:
      name: "Insulation Resistance"
    energy_production_day:
      name: "Daily Energy"
    total_energy_production:
      name: "Total Energy"
    inverter_module_temp:
      name: "Inverter Temperature"
    last_event_code:
      name: "Last Event Code"

text_sensor:
  - platform: sma_bluetooth
    sma_bluetooth_id: sma_hub
    mac_address: "00:80:25:AA:BB:CC"
    inverter_status:
      name: "Inverter Status"
    last_event:
      name: "Last Event Message"

binary_sensor:
  - platform: sma_bluetooth
    sma_bluetooth_id: sma_hub
    mac_address: "00:80:25:AA:BB:CC"
    grid_relay:
      name: "Grid Relay"
    inverter_fault:
      name: "Inverter Fault Active"
```

---

## ESP32 Configuration (Ethernet / WT32-ETH01)

For board stability with Ethernet + Bluetooth Classic, configure ESP-IDF memory slots in your device YAML:

```yaml
esp32:
  board: esp32dev
  framework:
    type: esp-idf
    sdkconfig_options:
      # Restrict BT Classic ACL slots to 1 to reserve heap for Ethernet & TCP streaming
      CONFIG_BTDM_CTRL_BR_EDR_MAX_ACL_CONN: "1"

# LAN8720 Ethernet wiring for WT32-ETH01:
ethernet:
  type: LAN8720
  mdc_pin: GPIO23
  mdio_pin: GPIO18
  clk_mode: GPIO0_IN
  phy_addr: 1
  power_pin: GPIO16
```

---

## Available Sensors

### Sensor Platform (Numeric)

| Key | Unit | Description |
|-----|------|-------------|
| `phase_a/b/c.voltage` | V | AC voltage per phase |
| `phase_a/b/c.current` | A | AC current per phase |
| `phase_a/b/c.active_power` | W | AC power per phase |
| `pv1/pv2.voltage` | V | DC voltage per MPPT / Strang |
| `pv1/pv2.current` | A | DC current per MPPT / Strang |
| `pv1/pv2.active_power` | W | DC power per MPPT / Strang |
| `frequency` | Hz | Grid frequency |
| `efficiency` | % | Real-time conversion efficiency ($P_{\text{AC}} / P_{\text{DC}} \times 100$) |
| `insulation_resistance` | kΩ | Pre-feed-in DC insulation resistance ($R_{\text{iso}}$) |
| `residual_current` | mA | Inverter DC/AC residual leakage current (Fehlerstrom) |
| `energy_production_day` | kWh | Daily energy yield |
| `total_energy_production` | kWh | Lifetime energy yield |
| `inverter_module_temp` | °C | Inverter heatsink / module temperature |
| `bt_signal_strength` | % | Bluetooth link quality |
| `today_generation_time` | h | Feed-in duration today |
| `total_generation_time` | h | Cumulative lifetime operating hours |
| `last_event_code` | – | Diagnostic SMA event code from memory buffer |
| `wakeup_time` | – | Timestamp of morning wakeup |

### Text Sensor Platform

| Key | Description |
|-----|-------------|
| `inverter_status` | Operating state (`Ok`, `Mpp`, `Disturbance`, `Fault`, `WaitGrid`, `Run`, `Shutdown`) |
| `last_event` | Full text description of the latest recorded inverter event or fault |
| `serial_number` | Inverter serial number |
| `software_version` | Firmware revision of the inverter controller |
| `device_type` | Inverter model designation (e.g. `SB 5000TL-20`, `SB 5000TL-21`) |
| `device_class` | SMA device class (e.g. `Solar Inverters`) |
| `grid_standard` | Country grid compliance profile / norm (e.g. `[DE] VDE-AR-N4105`, `[DE] VDE0126-1-1`) |
| `mac_address` | Bluetooth hardware address |
| `inverter_time` | Real-time clock of the inverter (synchronized with SNTP) |

> [!NOTE]
> Diagnostic device attributes (`serial_number`, `software_version`, `device_type`, `device_class`, `grid_standard`) can be defined either under the `text_sensor:` platform or directly within the `sensor:` platform block for concise YAML configs.

### Binary Sensor Platform

| Key | Description |
|-----|-------------|
| `grid_relay` | Internal grid disconnection relay state (closed = feeding in) |
| `inverter_fault` | Active fault state (`problem` device class, triggers on error events) |

---

## Historical Data HTTP Streaming (`/history`)

The component includes an on-demand HTTP streaming server on port 80. It reads data directly from the SMA inverter's internal flash memory ring buffer over Bluetooth and streams CSV data over TCP with chunked transfer, requiring virtually zero ESP32 RAM.

### 1. 5-Minute Spot Data (Power, Voltages, Currents)

Download granular 5-minute telemetry intervals (`ArchiveDayData`):

```http
GET http://<esp-ip>/history?type=spot&days=7
GET http://<esp-ip>/history?type=spot&days=all
GET http://<esp-ip>/history?type=spot&days=1&mac=00:80:25:AA:BB:CC
```

**CSV Output Format:**
```csv
Timestamp,Pac_W,Pdc1_W,Pdc2_W,Udc1_V,Udc2_V,Idc1_A,Idc2_A,Uac_V,Iac_A,E_Today_kWh,E_Total_kWh
2026-10-18 12:00:00,4820,2480,2410,380.5,385.2,6.51,6.25,231.4,20.82,21.45,108240.5
...
```

### 2. Daily Lifetime Yields Since Commissioning (`tageserträge`)

Download daily historical energy yields (`ArchiveMonthData`):

```http
GET http://<esp-ip>/history?type=daily&years=1
GET http://<esp-ip>/history?type=daily&years=all
GET http://<esp-ip>/history?type=daily&years=all&mac=00:80:25:AA:BB:CC
```

**CSV Output Format:**
```csv
Date,Energy_Total_kWh,Daily_Yield_kWh
2009-12-18,24.5,24.5
2009-12-19,38.2,13.7
...
```

### Query Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `type` | `spot`, `daily` | `spot` | Spot 5-minute data vs. daily energy totals |
| `days` | Integer or `all` | `1` | Number of past days for spot data |
| `years` | Integer or `all` | `1` | Number of past years for daily yield totals |
| `mac` | `AA:BB:CC:DD:EE:FF` | (all) | Target specific inverter in multi-inverter setups |

---

## How It Works

### Connection Lifecycle & Sequential Polling

The ESP32 maintains one active Bluetooth Classic SPP connection at a time. The hub manages sequential polling across configured or discovered inverters:

```
[GAP Scan / Cache] → [Connect Inv 1] → [Logon & RTC Sync] → [Read Sensors] → [Disconnect] → [Delay] → [Connect Inv 2] → ...
```

A full poll cycle for 2–3 inverters typically completes in 25–45 seconds.

### Inverter RTC Synchronization

During each logon sequence, the component compares the inverter's internal clock against the ESP32's synchronized SNTP time (`time::RealTimeClock`). If drift exceeds threshold, it issues time-synchronization packets (`0x00010000`), ensuring all historical ring buffer entries and fault timestamps match local wall clock time.

### Fault & Event Log Processing

The component queries active error and event buffers during the poll cycle. When fault flags or non-zero event codes are detected, `inverter_fault` is set to `ON` and `last_event` displays the decoded SMA event message (e.g. *DC overvoltage*, *Grid fault*, *Insulation failure*).

---

## Development & Testing

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture details and native unit tests.

### Run Unit Tests (Native PlatformIO)

```bash
pio test -e native
```

### Compile with ESPHome

Reference the component repository in your ESPHome configuration:

```yaml
external_components:
  - source: github://LeonhardFeiner/esphome_sma_bluetooth@main
    components: [sma_bluetooth]
```

---

## Credits

Forked and expanded from:
- [egnerfl/esphome_sma_bluetooth](https://github.com/egnerfl/esphome_sma_bluetooth)
- [keerekeerweere/esphome_smabluetooth](https://github.com/keerekeerweere/esphome_smabluetooth)
- [darrylb123/ESP32_SMA-Inverter-MQTT](https://github.com/darrylb123/ESP32_SMA-Inverter-MQTT)
- [SBFspot](https://github.com/SBFspot/SBFspot)

## License

MIT
