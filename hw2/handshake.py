import os
import hashlib
import struct

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding


PROTOCOL_LABEL = b"CSCE465-HS-v2"
GROUP_ID = b"ffdhe3072"
GROUP_FILE = Path("ffdhe3072.pem")

DH_PUBLIC_SIZE = 384

GATEWAY_IDENTITY = "gateway"
GATEWAY_ROLE = "gateway"
NODE_IDENTITY = "node"
NODE_ROLE = "node"


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


def encode_field(value: bytes) -> bytes:
    """
    Encode one transcript field as:

        4-byte big-endian length || value
    """
    return struct.pack(">I", len(value)) + value


def encode_dh_public(public_key: dh.DHPublicKey) -> bytes:
    """
    Encode an ffdhe3072 DH public value as exactly 384 bytes,
    big-endian, left-padded with zeroes when necessary.
    """
    y = public_key.public_numbers().y

    return y.to_bytes(
        DH_PUBLIC_SIZE,
        byteorder="big",
    )


def build_transcript(
    gateway_identity: str,
    node_identity: str,
    gateway_dh_pub_key: bytes,
    node_dh_pub_key: bytes,
    gateway_nonce: bytes,
    node_nonce: bytes
) -> bytes:
    """
    Encodes the transcript as its fields concatenated together, 
    each preceded by its length as a 4-byte big-endian integer.
    """
    fields = [
        PROTOCOL_LABEL,
        GROUP_ID,
        gateway_identity.encode("utf-8"),
        node_identity.encode("utf-8"),
        encode_dh_public(gateway_dh_pub_key),
        encode_dh_public(node_dh_pub_key),
        gateway_nonce,
        node_nonce,
    ]

    return b"".join(encode_field(field) for field in fields)


@dataclass
class Session:
    session_id: bytes = None
    peer_identity: str = None
    transcript: bytes = None
    transcript_hash: bytes = None


@dataclass
class Hello:
    identity: str
    dh_public_key: dh.DHPublicKey
    nonce: bytes


class Party:
    def __init__(
        self,
        identity: str,
        role: str,
        dh_parameters: dh.DHParameters,
        signing_key: rsa.RSAPrivateKey,
        trusted_peers: dict[str, rsa.RSAPublicKey],
        peer_role: str,
    ):
        self.identity = identity
        self.role = role
        self.group_id = GROUP_ID
        self.dh_parameters = dh_parameters
        self.signing_key = signing_key
        self.public_signing_key = signing_key.public_key()
        self.trusted_peers=trusted_peers
        self.peer_role = peer_role

        # per-handshake state
        self.dh_private_key = None
        self.dh_public_key = None
        self.nonce = None
        self.shared_secret = None

    def hello(self) -> Hello:
        """
        Generate a Hello containing the party identity, a fresh DH public key, 
        and a random 16 byte nonce.
        """
        self.dh_private_key = self.dh_parameters.generate_private_key()
        self.dh_public_key = self.dh_private_key.public_key()
        self.nonce = os.urandom(16)

        print(f"[*] Sending {self.identity} hello")

        return Hello(
            identity=self.identity,
            dh_public_key=self.dh_public_key,
            nonce=self.nonce
        )

    def sign(self, transcript_hash: bytes) -> bytes:
        """
        Sign role + transcript hash.
        """
        message = self.role.encode() + transcript_hash

        signature = self.signing_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        return signature

    def verify_signature(
        self,
        peer_identity: str,
        transcript_hash: bytes,
        signature: bytes,
    ) -> None:
        if peer_identity not in self.trusted_peers:
            raise ValueError(f"Unexpected peer identity: {peer_identity}")

        peer_public_key = self.trusted_peers[peer_identity]

        message = self.peer_role.encode() + transcript_hash

        peer_public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

    def compute_shared_secret(self, peer_dh_public_key: dh.DHPublicKey) -> None:
        """
        Compute the shared secret using the peer's DH public key.
        """
        pass


def derive_session_keys(self, shared_secret: bytes):
    """
    Derive session keys from the shared secret.
    """


def handshake(gateway: Party, node: Party) -> tuple[Session, Session]:
    """
    Perform the handshake between the gateway and node. 
    returns the established sessions for each party.
    """
    print(f"\nBeginning handshake between Gateway and Node")
    print(f"{'=' * 60}")

    gateway_hello = gateway.hello()
    node_hello = node.hello()

    transcript = build_transcript(
        gateway_hello.identity,
        node_hello.identity,
        gateway_hello.dh_public_key,
        node_hello.dh_public_key,
        gateway_hello.nonce,
        node_hello.nonce,
    )

    th = hashlib.sha256(transcript).digest()

    print(f"[*] Constructed transcript and computed transcript hash (th): {th.hex()}")
    
    gateway_signature = gateway.sign(transcript_hash=th)
    node_signature = node.sign(transcript_hash=th)

    gateway.verify_signature(
        peer_identity=node.identity,
        transcript_hash=th,
        signature=node_signature,
    )

    node.verify_signature(
        peer_identity=gateway.identity,
        transcript_hash=th,
        signature=gateway_signature,
    )

    gateway.compute_shared_secret(node_hello.dh_public_key)
    node.compute_shared_secret(gateway_hello.dh_public_key)

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
