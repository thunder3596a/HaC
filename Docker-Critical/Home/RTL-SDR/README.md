# RTL-SDR Service

Software-defined radio receiver using RTL-SDR USB dongle and rtl_433 for decoding 433 MHz signals.

## Setup

### 1. USB Device
Plug in your RTL-SDR dongle and verify it's detected:
```bash
lsusb | grep RTL
```

### 2. Configuration
Edit `/srv/rtl-sdr/config/rtl_433.conf` to customize:
- Frequency (default: 433.92 MHz)
- Protocols to decode
- Output format
- Gain settings

### 3. MQTT Integration
Set these Forgejo variables:
- `MQTT_HOST` - MQTT broker hostname (default: homeassistant)
- `MQTT_PORT` - MQTT broker port (default: 1883)
- `MQTT_USER` - MQTT username
- `MQTT_PASSWORD` (secret) - MQTT password

### 4. Deploy
```bash
# Via Forgejo workflow (automatic on push)
# Or manually:
docker compose -p rtl-sdr -f rtl-sdr.yml up -d
```

## Home Assistant Integration

Once running, rtl_433 will publish decoded sensor data to MQTT topics like:
```
rtl_433/[model]/[id]
```

Add MQTT integration in Home Assistant to auto-discover these sensors.

## Supported Devices

Common 433 MHz devices that rtl_433 can decode:
- Weather stations (Acurite, LaCrosse, Fine Offset, etc.)
- Temperature/humidity sensors
- Tire pressure monitors
- Wireless doorbells
- Remote controls
- Power meters

## Troubleshooting

### No USB device found
```bash
# Check USB permissions
ls -l /dev/bus/usb/*/*

# May need udev rules for non-root access
```

### No signals received
- Check antenna connection
- Verify frequency matches your devices
- Adjust gain (try manual gain vs auto)
- Check for USB hub issues (some hubs cause problems)

### MQTT not connecting
- Verify MQTT broker is running
- Check credentials
- Ensure network connectivity between containers
