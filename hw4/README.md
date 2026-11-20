# CSCE 465 HW 4: Detect and Block Agent Exfiltration

## Setup

Install the the required software in the Ubuntu VM

### Docker Engine and Compose

```sh
sudo apt remove -y docker.io docker-compose docker-compose-v2 containerd runc 2>/dev/null || true
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF_DOCKER
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF_DOCKER
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

### Nmap, tcpdump, TShark, netcat, Suricata

```sh
sudo apt install -y nmap tcpdump tshark netcat-openbsd
sudo add-apt-repository -y ppa:oisf/suricata-stable
sudo apt update
sudo apt install -y suricata
sudo usermod -aG suricata "$USER"
```

Log out and back in, and confirm installation was successful

```sh
docker run --rm hello-world
docker compose version
nmap --version
tshark --version
suricata -V
```

## Task 1: Build the local network lab

### Setup



## Task 2: Scan, capture, and reconstruct the event



## Task 3: Default-deny egress for the agent container



## Task 4: Three Suricata rules


