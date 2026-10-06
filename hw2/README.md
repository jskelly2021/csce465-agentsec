# CSCE 465 HW 2: Protect Agent Messages with Classic Cryptography

## Setup

The lab expects Ubuntu 24.04 LTS x86-64.

### Clone the repo

```sh
git clone https://github.com/jskelly2021/csce465-agentsec.git
cd csce465-agentsec
```

### Setup the python environment

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install cryptography==49.0.0 pytest==9.1.1
cd hw2
```

### Generate a standard ffdhe3072 parameter file

```sh
openssl genpkey -genparam -algorithm DH -pkeyopt group:ffdhe3072 -out ffdhe3072.pem
openssl dhparam -in ffdhe3072.pem -text -noout | head -3
```

## Task 1

Run `baseline_ctr.py` experiment.

```sh
python baseline_ctr.py
```

## Task 2

Run `handshake.py` experiment.

```sh
python handshake.py
```

## Run Tests

TODO
