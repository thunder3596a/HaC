**Kiwix Local Library (Doomsday Library)**

- **Purpose**: Serve a fully local, offline Kiwix library (ZIM files) from your TrueNAS / local host.
- **Location**: `HaC/Docker-Critical/Home/Doomsday` (this compose file and helpers)

**Overview**
- Put your `.zim` files on the host at `/mnt/Apps/kiwix/zim` (create this dataset on TrueNAS and upload ZIMs there).
- Use the provided `library.yml` (docker-compose) to run `kiwix-serve` and expose the UI on `http://<host>:8080`.
- Run the included `generate-library.sh` helper to create or update `library.xml` using the official `ghcr.io/kiwix/kiwix-tools` image.

Prerequisites
- TrueNAS Scale (or other Linux host) with Docker/Containerd support and a dataset mounted at `/mnt/Apps/kiwix/zim`.
- ZIM files placed in `/mnt/Apps/kiwix/zim`.

Steps
1) Create the data directory on TrueNAS (run on TrueNAS shell):
```powershell
mkdir -p /mnt/Apps/kiwix/zim
chmod 755 /mnt/Apps/kiwix/zim
```

2) Copy ZIM files into `/mnt/Apps/kiwix/zim` (via SMB, scp, or TrueNAS UI).

3) Generate the Kiwix `library.xml`:

Run the helper script on the host (gives command variants):
```bash
bash generate-library.sh
```

Then run one of the suggested `docker run` commands printed by the script — example:
```bash
docker run --rm -v /mnt/Apps/kiwix/zim:/data ghcr.io/kiwix/kiwix-tools kiwix-manage /data/library.xml add /data/*.zim
```

If that syntax fails, run the help to find the right subcommand:
```bash
docker run --rm -v /mnt/Apps/kiwix/zim:/data ghcr.io/kiwix/kiwix-tools kiwix-manage --help
```

4) Start Kiwix server (docker-compose):
```bash
docker-compose -f library.yml pull
docker-compose -f library.yml up -d
```

5) Open the web UI: http://<truenas-host>:8080

Notes & Tips
- The `kiwix-serve` container reads `/data/library.xml` and serves all mounted `.zim` files. If you add/remove ZIMs, re-run the library generation step and restart `kiwix-serve`.
- For reproducible automation you can run the `kiwix-tools` command inside a CI job or a periodic cronjob on the host to update `library.xml`.
- If you prefer non-container setup, install `kiwix-tools` on a Linux VM and run `kiwix-manage` locally.

Security
- Serving ZIMs locally is safe; avoid exposing the port publicly unless you secure it behind your proxy or with firewall rules.

Troubleshooting
- If `kiwix-serve` doesn't find any ZIMs, verify `/mnt/Apps/kiwix/zim` is mounted into the container and contains `.zim` files.
- If `kiwix-manage` subcommands differ between versions, run `docker run --rm ghcr.io/kiwix/kiwix-tools kiwix-manage --help` to find correct syntax.

If you want, I can:
- Add an automated `watch` container that regenerates `library.xml` when new ZIMs appear, or
- Add Traefik labels to serve the Kiwix UI behind your proxy (let me know hostnames and network).
