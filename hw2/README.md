# CSCE 465 HW 2: Protect Agent Messages with Classic Cryptography

## Setup

The lab expects Ubuntu 24.04 LTS x86-64.

### Clone the repo

`git clone https://github.com/jskelly2021/csce465-agentsec.git`

### Setup the python environment

```sh
cd csce465-agentsec
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install cryptography==49.0.0 pytest==9.1.1
```

### Generate a standard ffdhe3072 parameter file

```sh
cd hw2
openssl genpkey -genparam -algorithm DH -pkeyopt group:ffdhe3072 -out ffdhe3072.pem
openssl dhparam -in ffdhe3072.pem -text -noout | head -3
```

## Task 1

Run `baseline_ctr.py` experiment.

```sh
python baseline_ctr.py
```

## Run Tests

TODO
