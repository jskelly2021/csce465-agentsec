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

### Setup the docker environment

Build and run the containers.

```sh
docker compose up -d --build
```

Confirm the containers are running.

```sh
docker compose ps
```

Confirm the network name.

```sh
docker network ls
```

Inspect the network. Use the name of the network discovered in the previous step.

```sh
docker network inspect hw4_hw4net
```

### Run the experiment

Verify the secret has not been received by the c2.

```sh
docker compose exec mock-c2 ls -l /data/received.bin
```

If the secret already exists

```sh
docker compose exec mock-c2 rm -f /data/received.bin
```

Run the exfiltration

```sh
docker compose exec agent-node sh /app/mock_skill.sh exfiltrate-course-file
```

Check if exfiltration was successful.

```sh
docker compose exec mock-c2 ls -l /data/received.bin
```

### Verify exfiltration

Verify the contents of agent-node's secret and mock-c2's received secret.

```sh
docker compose exec agent-node sha256sum /app/fake_secrets.txt
docker compose exec mock-c2 sha256sum /data/received.bin
```

## Task 2: Scan, capture, and reconstruct the event



## Task 3: Default-deny egress for the agent container



## Task 4: Three Suricata rules


