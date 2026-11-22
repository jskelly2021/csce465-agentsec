# CSCE 465 HW 4: Detect and Block Agent Exfiltration

## Setup

All commands should be executed from the HW4 directory.

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

Verify all 3 containers are running.

```sh
docker compose ps
```

### Nmap Port Scan

Execute the mock skill on agent-node with no arguments to start the TCP listener.

```sh
docker compose exec agent-node ./mock_skill.sh
```

In a new terminal on the host VM, use nmap to port scan agent-node.

```sh
nmap -sT -p 1-10000 172.30.0.10
```

### Malicious Incident Capture

On the host VM, start a packet capture with tcpdump

```sh
sudo tcpdump -i br-hw4 -s 0 -w hw4-malicious.pcap 'net 172.30.0.0/24'
```

In a new terminal, fetch the adversarial page, then trigger the mock skill to exfiltrate the secret. Then end the capture.

```sh
docker compose exec agent-node curl http://172.30.0.40:8000/adversarial.html
docker compose exec agent-node ./mock_skill.sh exfiltrate-course-file
```

### Reconstruction

Extract connection details

```sh
tshark -r hw4-malicious.pcap \
  -Y 'http.request' \
  -T fields \
  -e ip.src -e tcp.srcport \
  -e ip.dst -e tcp.dstport \
  -e http.request.method \
  -e http.request.uri \
  -e tcp.stream
```

Follow the exfiltration TCP stream. Replace `N` with thte TCP stream number.

```sh
tshark -r hw4-malicious.pcap -q -z follow, tcp, ascii, N
```

Retrieve the first and last packet timestamps. Replace `N` with thte TCP stream number.

```sh
tshark -r hw4-malicious.pcap \
  -Y 'tcp.stream == 1' \
  -T fields -e frame.time
```

Extract the POST body.

```sh
mkdir -p objs
tshark -r hw4-malicious.pcap -q --export-objects http,objs/
```

Compute the hash of the POST body

```sh
ls -l objs/
sha256sum objs/<POST_BODY_FILENAME>
```

### Clean Capture

On the host VM, start a packet capture with tcpdump

```sh
sudo tcpdump -i br-hw4 -s 0 -w hw4-clean.pcap 'net 172.30.0.0/24'
```

In a new terminal, fetch the benign page, then end the capture.

```sh
docker compose exec agent-node curl http://172.30.0.40:8000/benign.html
```

## Task 3: Default-deny egress for the agent container



## Task 4: Three Suricata rules


