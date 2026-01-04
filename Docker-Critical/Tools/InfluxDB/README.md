# InfluxDB

Time-series database for storing and querying metrics, sensor data, and historical statistics from Home Assistant and other sources.

## Overview

InfluxDB 2.x is a modern time-series database optimized for:

- **Home Automation Metrics** - Temperature, humidity, energy consumption from sensors
- **Historical Data** - Long-term trend analysis and archiving
- **Performance Monitoring** - Track system resource usage and service metrics
- **Data Analysis** - Complex queries and aggregations over time

## Configuration

### First Run

1. Access the dashboard at `influx.${DOMAIN_NAME}`
2. Create initial admin credentials (already set via secrets)
3. Create organization and bucket for Home Assistant data
4. Generate API token for Home Assistant integration

### Environment Variables

- `INFLUXDB_ADMIN_USER` - Initial admin username (default: `admin`)
- `INFLUXDB_ADMIN_PASSWORD` - Admin password (set via Forgejo secrets)
- `INFLUXDB_DB` - Initial database name (default: `homeautomation`)
- `TZ` - Timezone (default: `America/Chicago`)
- `INFLUXDB_HTTP_AUTH_ENABLED` - Authentication enforcement (default: `true`)

### Forgejo Secrets Required

- `INFLUXDB_ADMIN_PASSWORD` - Strong admin password for initial setup

### Forgejo Variables Optional

- `INFLUXDB_ADMIN_USER` - Admin username (default: `admin`)

## Home Assistant Integration

### Setup Steps

1. **Install Integration** - Home Assistant → Settings → Devices & Services → Create Automation
2. **Configure Connection** - Point to `http://influxdb:8086`
3. **Generate API Token**:
   - Open InfluxDB dashboard
   - API Tokens → Generate Token → All Access
   - Copy token and paste into HA configuration
4. **Select Entities** - Choose which entities to record to InfluxDB

### Configuration Example (Home Assistant configuration.yaml)

```yaml
influxdb:
  api_version: 2
  ssl: false
  host: influxdb
  port: 8086
  token: !secret influxdb_token
  organization: HomeAutomation
  bucket: homeassistant
  tags:
    instance: home
    environment: production
  tags_attributes:
    - friendly_name
  default_measurement: units
```

## Data Management

### Buckets

Organize data by retention and purpose:

- **homeautomation** - All sensor/entity data (14-30 day retention)
- **history** - Long-term archive (1+ year retention)
- **diagnostics** - System metrics (7 day retention)

### Retention Policies

Configure in InfluxDB UI:

1. Navigate to Buckets
2. Select bucket → Edit Retention
3. Set retention duration (e.g., 30 days)

### Backup Data

```bash
# Export bucket to file
docker exec influxdb influx backup /var/lib/influxdb2/backup

# Copy backup locally
docker cp influxdb:/var/lib/influxdb2/backup ./influxdb-backup-$(date +%Y%m%d)
```

## Queries & Analysis

### Common Queries

**Last 24 hours average:**
```flux
from(bucket: "homeautomation")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "°C")
  |> aggregateWindow(every: 1h, fn: mean)
```

**Compare current vs. previous week:**
```flux
union(
  tables: [
    from(bucket: "homeautomation") |> range(start: -7d) |> filter(fn: (r) => r["_field"] == "value"),
    from(bucket: "homeautomation") |> range(start: -14d, stop: -7d) |> filter(fn: (r) => r["_field"] == "value")
  ]
)
```

**Energy consumption total:**
```flux
from(bucket: "homeautomation")
  |> range(start: 2025-01-01, stop: 2025-02-01)
  |> filter(fn: (r) => r["_measurement"] == "kWh")
  |> sum()
```

## Grafana Integration

### Setup with Grafana

1. Add InfluxDB data source in Grafana
   - URL: `http://influxdb:8086`
   - Organization: `HomeAutomation`
   - Token: (API token from InfluxDB)
   - Bucket: `homeautomation`

2. Create dashboards querying InfluxDB data

## Data Paths

```
/srv/influxdb/
├── data/                # Time-series database files
└── config/              # Configuration and custom settings
```

## Ports

- **8086** - HTTP API (Traefik routing + direct access)

## Performance Tips

1. **Selective Recording** - Only store necessary entities in Home Assistant
2. **Shard Duration** - Large datasets use longer shard duration (7d vs default 24h)
3. **Downsampling** - Create continuous queries to downsample old data
4. **Index Strategy** - Tag frequently filtered fields (entity_id, friendly_name)

## Troubleshooting

### Cannot Connect from Home Assistant

```bash
# Verify InfluxDB is running
docker ps | grep influxdb

# Check logs for errors
docker logs influxdb

# Test connectivity from HA container
docker exec homeassistant curl -i http://influxdb:8086/health
```

### High Disk Usage

```bash
# Check bucket sizes
docker exec influxdb influx bucket list

# View disk usage
du -sh /srv/influxdb/data/

# Reduce retention or delete old buckets
```

### Slow Queries

```bash
# Check task execution
docker exec influxdb influx task list

# Monitor system resources
docker stats influxdb

# Consider adding more RAM if system swapping
```

## Resources

- [InfluxDB 2.x Docs](https://docs.influxdata.com/influxdb/v2.7/)
- [Flux Query Language](https://docs.influxdata.com/flux/latest/)
- [InfluxDB Home Assistant Integration](https://www.home-assistant.io/integrations/influxdb/)
- [InfluxDB API Reference](https://docs.influxdata.com/influxdb/v2.7/api/)

## License

InfluxDB is available under multiple licenses (open source and commercial).
