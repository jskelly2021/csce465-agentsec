import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa


GROUP_FILE = Path("ffdhe3072.pem")
GROUP_ID = "ffdhe3072"


class Transcript:
    def __init__(self,
        protocol: str,
        group: str,
        gateway_identity: str,
        node_identity: str,
        gateway_DH_public: bytes,
        node_DH_public: bytes,
        gateway_nonce: bytes,
        node_nonce: bytes    
    ):
        self.protocol = protocol
        self.group = group
        self.gateway_identity = gateway_identity
        self.node_identity = node_identity
        self.gateway_DH_public = gateway_DH_public
        self.node_DH_public = node_DH_public
        self.gateway_nonce = gateway_nonce
        self.node_nonce = node_nonce

    def encode(self) -> bytes:
        """
        Encodes the transcript as its fields concatenated together, each preceded by its length as a 4-byte big-endian integer.
        """
        pass

    def hash(self) -> bytes:
        pass


class Session:
    def __init__(self):
        self.session_id = None
        self.peer_identity = None
        self.transcript = None
        self.transcript_hash = None


@dataclass
class HandshakeState:
    dh_private_key: dh.DHPrivateKey
    dh_public_key: dh.DHPublicKey
    nonce: bytes


class Party:
    def __init__(
        self,
        identity: str,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
    ):
        self.identity = identity
        self.group_id = GROUP_ID
        self.dh_parameters = dh_parameters
        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()
        self.trusted_peers=trusted_peers,

    def begin_handshake(self) -> HandshakeState:
        """
        Generate a HandshakeState containing the fresh DH key pair, and random 16 byte nonce.
        """
        dh_private_key = self.dh_parameters.generate_private_key()
        dh_public_key = dh_private_key.public_key()
        nonce = os.urandom(16)

        print(f"{f'[{self.identity}]':<9} Generated DH key pair and nonce for handshake")

        return HandshakeState(
            dh_private_key=dh_private_key,
            dh_public_key=dh_public_key,
            nonce=nonce
        )


def load_dh_parameters(path: Path) -> dh.DHParameters:
    """
    Load the finite-field DH parameters from the PEM group file.
    """
    with path.open("rb") as f:
        parameters = serialization.load_pem_parameters(f.read())

    if not isinstance(parameters, dh.DHParameters):
        raise TypeError("Group file does not contain DH parameters")

    return parameters


def generate_rsa_signing_key() -> rsa.RSAPrivateKey:
    """
    Generate 3072-bit RSA signing key.
    """
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072,
    )


def handshake(gateway: Party, node: Party) -> tuple[Session, Session]:
    """
    Perform the handshake between the gateway and node. returns the established sessions for each party.
    """
    gateway_state = gateway.begin_handshake()
    node_state = node.begin_handshake()

    gateway_session = Session()
    node_session = Session()

    return gateway_session, node_session


def main():
    dh_parameters = load_dh_parameters(GROUP_FILE)

    print(f"[*] Loaded DH parameters from {GROUP_FILE} (group ID: {GROUP_ID})")

    gateway_signing_key = generate_rsa_signing_key()
    node_signing_key = generate_rsa_signing_key()

    print(f"[*] Generated RSA signing keys for Gateway and Node")

    gateway = Party(
        identity="gateway",
        dh_parameters=dh_parameters,
        signing_key=gateway_signing_key,
        trusted_peers={
            "node": node_signing_key.public_key(),
        },
    )

    node = Party(
        identity="node",
        dh_parameters=dh_parameters,
        signing_key=node_signing_key,
        trusted_peers={
            "gateway": gateway_signing_key.public_key(),
        },
    )

    print(f"[*] Initialized Gateway and Node")

    print(f"\n{'=' * 40}")
    print(f"HANDSHAKE SIMULATION")
    print(f"{'=' * 40}")

    gateway_session, node_session = handshake(gateway, node)

    print("")


if __name__ == "__main__":
    main()
