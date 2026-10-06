from pathlib import Path

import pytest

from handshake import (
    GATEWAY_IDENTITY,
    GATEWAY_ROLE,
    NODE_IDENTITY,
    NODE_ROLE,
    Party,
    generate_rsa_signing_key,
    handshake,
    load_dh_parameters,
)


GROUP_FILE = Path(__file__).resolve().parents[1] / "ffdhe3072.pem"


@pytest.fixture(scope="session")
def dh_parameters():
    return load_dh_parameters(GROUP_FILE)


@pytest.fixture(scope="session")
def signing_keys():
    gateway_key = generate_rsa_signing_key()
    node_key = generate_rsa_signing_key()

    return gateway_key, node_key


@pytest.fixture
def parties(dh_parameters, signing_keys):
    gateway_key, node_key = signing_keys

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_key,
        trusted_peers={
            NODE_IDENTITY: node_key.public_key(),
        },
        peer_role=NODE_ROLE,
    )

    node = Party(
        identity=NODE_IDENTITY,
        role=NODE_ROLE,
        dh_parameters=dh_parameters,
        signing_key=node_key,
        trusted_peers={
            GATEWAY_IDENTITY: gateway_key.public_key(),
        },
        peer_role=GATEWAY_ROLE,
    )

    return gateway, node


@pytest.fixture
def sessions(parties):
    gateway, node = parties

    return handshake(gateway, node)
