import pytest

from cryptography.exceptions import InvalidSignature

from handshake import (
    GATEWAY_IDENTITY,
    GATEWAY_ROLE,
    NODE_IDENTITY,
    NODE_ROLE,
    Party,
    generate_rsa_signing_key,
    handshake,
)


def test_incorrect_rsa_public_key_rejected(
    dh_parameters,
    signing_keys,
):
    gateway_key, node_key = signing_keys

    wrong_node_key = generate_rsa_signing_key()

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_key,
        trusted_peers={
            NODE_IDENTITY: wrong_node_key.public_key(),
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

    with pytest.raises(InvalidSignature):
        handshake(gateway, node)
