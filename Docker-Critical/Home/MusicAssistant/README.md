# Music Assistant

Music server and player management system for your home automation setup. Supports multiple music sources and player types with comprehensive music library management.

## Overview

Music Assistant is a music streaming server that integrates with Home Assistant and supports numerous music providers and player devices. It provides:

- **Unified Library:** Merge music from multiple providers (Spotify, Plex, Jellyfin, local files, etc.)
- **Multi-Provider Support:** Connect to Spotify, Apple Music, Tidal, Qobuz, and many more
- **Player Management:** Control AirPlay, Sonos, Google Cast, DLNA, and other player types
- **Smart Library:** Browse, search, and organize your music across all sources
- **Quality Selection:** Automatically plays highest quality available from configured providers

## Configuration

### First Run

1. Access the dashboard at `music.${DOMAIN_NAME}`
2. Configure music providers (Spotify, Plex, local files, etc.)
3. Add player devices (Sonos, AirPlay speakers, etc.)
4. Enable integrations (Spotify Connect, AirPlay Receiver, etc.)

### Environment Variables

- `TZ` - Timezone (default: `America/Chicago`)
- `LOG_LEVEL` - Logging level (default: `info`, options: `critical`, `error`, `warning`, `debug`)
- `DOMAIN_NAME` - Primary domain for Traefik routing

### Music Providers

Music Assistant supports numerous music sources. Configure in settings:

- **Local Files** - Mount `/media/music` for local FLAC/MP3 files
- **Streaming Services** - Spotify, Apple Music, Tidal, Qobuz, SoundCloud, YouTube Music
- **Self-Hosted** - Jellyfin, Plex, Subsonic, iBroadcast
- **Radio** - TuneIn, Radio Browser, Radio Paradise, DI.fm
- **Podcasts** - Podcast RSS, Podcast Index, iTunes Podcast Search

### Player Providers

Supported player types:

- **AirPlay** - Apple speakers, AirPlay-enabled devices
- **Sonos** - Sonos speakers and systems
- **Google Cast** - Chromecast, Google Home, Nest
- **Spotify Connect** - Spotify playback control
- **DLNA** - DLNA/UPnP compatible devices
- **Bluesound** - Bluesound speakers
- **MusicCast** - Yamaha MusicCast devices
- **Snapcast** - Network audio synchronization

## Network Requirements

**CRITICAL:** Music Assistant requires `network_mode: host` for proper operation:

1. **mDNS Discovery** - Finds players on local network via Bonjour/Zeroconf
2. **Player Streaming** - Streams audio directly to players (TCP 8097 by default)
3. **Same Network** - MA and all players must be on the same flat network (no VLANs)

## Data Paths

```
/srv/music-assistant/
├── data/              # Configuration, database, cache
├── data/config/       # User settings and configurations
└── data/library/      # Music library metadata
```

## Media Access

Local music files are mounted read-only:

```
/mnt/Pool01/data/media/music/ → /media/music
```

Browse and add to library via Music Assistant settings.

## Ports

- **8095** - Web interface (dashboard)
- **8097** - Audio streaming port (TCP, required for players)

These are automatically managed by the compose configuration and Traefik routing.

## Integration with Home Assistant

Music Assistant integrates with Home Assistant via:

1. **HA Integration** - Install from Home Assistant Integrations
2. **Service Calls** - Play media, announcements, search
3. **Media Player** - Control playback from automations
4. **Custom Lovelace** - Add Music Assistant UI to dashboard

## Troubleshooting

### Players Not Discoverable

```bash
# Check logs for mDNS discovery
docker logs music-assistant | grep -i discovery

# Verify host network mode
docker inspect music-assistant | grep -A 5 "NetworkMode"

# Ensure no VLANs between MA and players
# Verify players support mDNS/Bonjour
```

### Slow Library Sync

Initial library sync from multiple providers can take time:

1. Check sync progress in MA settings (sync icon)
2. Large libraries (10k+ tracks) may take hours
3. Subsequent syncs are much faster (incremental)
4. Monitor logs: `docker logs music-assistant -f`

### Audio Streaming Issues

```bash
# Verify streaming port is available
netstat -tlnp | grep 8097

# Check firewall isn't blocking ports
# Ensure players can reach host on TCP 8097

# If port conflict, configure in MA settings (Settings → Core)
```

### Provider Authentication

Each provider requires separate configuration:

1. Open Music Assistant settings
2. Navigate to Music Provider Settings
3. Add credentials/auth tokens for each service
4. Grant permissions if prompted (Spotify, Apple Music, etc.)

## Performance Notes

- **Minimum RAM:** 2GB (4GB+ recommended if running Home Assistant too)
- **CPU:** Requires 64-bit processor (max age: 10 years for Intel, 5 years for AMD)
- **Disk:** Config uses minimal space (<100MB), library metadata varies by size
- **Playlist Limit:** Keep playlists/queues under 1000 items for stability

## Resources

- [Music Assistant Docs](https://www.music-assistant.io/)
- [Music Assistant Discord](https://discord.gg/kaVm8hGpne)
- [GitHub Repository](https://github.com/music-assistant)
- [Music Providers Catalog](https://www.music-assistant.io/music-providers/)
- [Player Support Matrix](https://www.music-assistant.io/player-support/)

## License

Music Assistant is free and open source, maintained by the Open Home Foundation.
