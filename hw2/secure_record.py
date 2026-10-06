import struct

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from handshake import (
    GROUP_ID, GROUP_FILE,
    GATEWAY_IDENTITY, GATEWAY_ROLE,
    NODE_IDENTITY, NODE_ROLE,
    GATEWAY_TO_NODE, NODE_TO_GATEWAY,
    load_dh_parameters,
    generate_rsa_signing_key,
    Party, Session,
    handshake,
)


VERSION = 1
TAG_SIZE = 32
IV_SIZE = 16

HEADER_STRUCT = struct.Struct(">BBQBI")
HEADER_SIZE = HEADER_STRUCT.size


def open_record(
    session: Session,
    record: bytes,
) -> tuple[bytes, bytes]:
    pass


def seal(
    session: Session,
    plaintext: bytes,
    message_type: int,
) -> bytes:
    pass


def main():
    dh_parameters = load_dh_parameters(GROUP_FILE)

    print(f"[*] Loaded DH parameters from {GROUP_FILE} (group ID: {GROUP_ID})")

    gateway_signing_key = generate_rsa_signing_key()
    node_signing_key = generate_rsa_signing_key()

    print(f"[*] Generated long-term RSA signing keys for Gateway and Node")

    gateway = Party(
        identity=GATEWAY_IDENTITY,
        role=GATEWAY_ROLE,
        dh_parameters=dh_parameters,
        signing_key=gateway_signing_key,
        trusted_peers={
            NODE_IDENTITY: node_signing_key.public_key(),
        },
        peer_role=NODE_ROLE
    )

    node = Party(
        identity=NODE_IDENTITY,
        role=NODE_ROLE,
        dh_parameters=dh_parameters,
        signing_key=node_signing_key,
        trusted_peers={
            GATEWAY_IDENTITY: gateway_signing_key.public_key(),
        },
        peer_role=GATEWAY_ROLE
    )

    print(f"[*] Initialized Gateway and Node")

    gateway_session, node_session = handshake(gateway, node)

    print("")


if __name__ == "__main__":
    main()
