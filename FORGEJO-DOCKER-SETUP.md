# Forgejo Runner & Docker Setup on Debian (Trixie)

This guide documents the step-by-step process for installing Docker, Docker Compose, and Forgejo Actions Runner on a Debian (Trixie/testing) host, including troubleshooting for common issues.

---

## 1. System Preparation

**Update and install required tools:**
```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates gnupg jq
```

---

## 2. Docker Installation (Debian Trixie)

> **Note:** Docker's official repo does not fully support Debian testing/unstable. You may encounter dependency issues. For production, use Debian stable/bookworm.

**Run the official install script:**
```sh
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**If you see dependency errors (e.g., libxtables12, iptables):**
```sh
sudo apt-get install libxtables12=1.8.9-2 iptables
sudo sh get-docker.sh
```

---

## 3. Docker Compose Installation

> The `docker-compose` package may not work due to Python version conflicts. Use the official binary:

```sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Test:**
```sh
docker-compose --version
```

---

## 4. Forgejo Actions Runner Installation

**Download and verify the latest runner:**
```sh
export ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')
export RUNNER_VERSION=$(curl -s https://data.forgejo.org/api/v1/repos/forgejo/runner/releases/latest | jq .name -r | cut -c 2-)
export FORGEJO_URL="https://code.forgejo.org/forgejo/runner/releases/download/v${RUNNER_VERSION}/forgejo-runner-${RUNNER_VERSION}-linux-${ARCH}"

wget -O forgejo-runner "$FORGEJO_URL" || curl -o forgejo-runner "$FORGEJO_URL"
sudo mv forgejo-runner /opt/forgejo-runner
sudo chmod +x /opt/forgejo-runner

wget -O forgejo-runner.asc "$FORGEJO_URL.asc" || curl -o forgejo-runner.asc "$FORGEJO_URL.asc"
gpg --keyserver hkps://keys.openpgp.org --recv EB114F5E6C0DC2BCDD183550A4B61A2DC5923710
gpg --verify forgejo-runner.asc /opt/forgejo-runner && echo "✓ Verified" || echo "✗ Failed"
```

---

## 5. Register and Run Forgejo Runner

**Register the runner:**
```sh
/opt/forgejo-runner register --instance https://git.<your-domain> --token <your-token> --labels docker-noncritical:host
```

**Create a systemd service:**
```sh
sudo nano /etc/systemd/system/forgejo-runner.service
```
Paste:
```
[Unit]
Description=Forgejo Actions Runner
After=network.target

[Service]
Type=simple
ExecStart=/opt/forgejo-runner run --instance https://git.<your-domain> --token <your-token> --labels docker-noncritical:host
Restart=always
User=root
WorkingDirectory=/opt

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**
```sh
sudo systemctl daemon-reload
sudo systemctl enable forgejo-runner
sudo systemctl start forgejo-runner
sudo systemctl status forgejo-runner
```

---

## 6. Troubleshooting

- If Docker is not installed as a service:
  - Remove old packages: `sudo apt remove docker wmdocker`
  - Reinstall using the official script.
- If you encounter dependency errors, manually install required packages as shown above.
- For Python version issues with Compose, always use the official binary.

---

## 7. Migrating Runner from Another Host

**Copy runner and service from another host:**
```sh
scp -r root@<old-host>:/opt/forgejo-runner /opt/forgejo-runner
scp root@<old-host>:/etc/systemd/system/forgejo-runner.service /etc/systemd/system/forgejo-runner.service
sudo chmod +x /opt/forgejo-runner/forgejo-runner
sudo systemctl daemon-reload
sudo systemctl enable forgejo-runner
sudo systemctl start forgejo-runner
```

---

## References
- [Forgejo Runner Releases](https://code.forgejo.org/forgejo/runner/releases)
- [Docker Install Script](https://get.docker.com)
- [Docker Compose Releases](https://github.com/docker/compose/releases)

---

**Last updated:** January 15, 2026
