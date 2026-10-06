import os
import hashlib
import struct
import hmac

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding


PROTOCOL_LABEL = b"CSCE465-HS-v2"
GROUP_ID = b"ffdhe3072"
GROUP_FILE = Path("ffdhe3072.pem")

DH_VALUE_SIZE = 384

GATEWAY_IDENTITY = "gateway"
GATEWAY_ROLE = "gateway"
NODE_IDENTITY = "node"
NODE_ROLE = "node"


@dataclass(frozen=True)
class SessionKeys:
    g2n_enc: bytes
    g2n_mac: bytes
    n2g_enc: bytes
    n2g_mac: bytes
    session_id: bytes


@dataclass
class Session:
    session_id: bytes
    send_enc_key: bytes
    send_mac_key: bytes
    recv_enc_key: bytes
    recv_mac_key: bytes


@dataclass(frozen=True)
class Hello:
    identity: str
    dh_public_key: dh.DHPublicKey
    nonce: bytes


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
        DH_VALUE_SIZE,
        byteorder="big",
    )


def build_transcript(
    gateway_identity: str,
    node_identity: str,
    gateway_dh_pub_key: dh.DHPublicKey,
    node_dh_pub_key: dh.DHPublicKey,
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


def kdf(z: bytes, transcript_hash: bytes) -> SessionKeys:
    """
    Apply the KDF.
    """
    if len(z) != DH_VALUE_SIZE:
        raise ValueError("Z must be exactly 384 bytes")

    # K_master = SHA-256("CSCE465-KDF-v1" || Z || TH)
    k_master = hashlib.sha256(
        b"CSCE465-KDF-v1"
        + z
        + transcript_hash
    ).digest()

    def derive(label: bytes) -> bytes:
        return hmac.new(
            k_master,
            label + transcript_hash,
            hashlib.sha256,
        ).digest()

    k_g2n_enc = derive(b"gateway-to-node encryption")
    k_g2n_mac = derive(b"gateway-to-node MAC")
    k_n2g_enc = derive(b"node-to-gateway encryption")
    k_n2g_mac = derive(b"node-to-gateway MAC")

    session_id = derive(b"session identifier")[:8]

    return SessionKeys(
        g2n_enc=k_g2n_enc,
        g2n_mac=k_g2n_mac,
        n2g_enc=k_n2g_enc,
        n2g_mac=k_n2g_mac,
        session_id=session_id,
    )


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
        self.th = None

    def hello(self) -> Hello:
        """
        Generate a Hello containing the party identity, a fresh DH public key, 
        and a random 16 byte nonce.
        """
        self.dh_private_key = self.dh_parameters.generate_private_key()
        self.dh_public_key = self.dh_private_key.public_key()
        self.nonce = os.urandom(16)

        print(f"[*] {self.identity} generated fresh DH key pair and 16-byte nonce")\

        return Hello(
            identity=self.identity,
            dh_public_key=self.dh_public_key,
            nonce=self.nonce
        )

    def hash_transcript(self, transcript: bytes) -> bytes:
        self.th = hashlib.sha256(transcript).digest()
        return self.th

    def sign(self) -> bytes:
        """
        Sign role + transcript hash.
        """
        if self.th is None:
            raise ValueError("Transcript hash has not been computed")

        message = self.role.encode() + self.th

        signature = self.signing_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        print(f"[*] {self.identity} signed transcript hash")

        return signature

    def verify_signature(
        self,
        peer_identity: str,
        signature: bytes,
    ) -> None:
        if self.th is None:
            raise ValueError("Transcript hash has not been computed")

        if peer_identity not in self.trusted_peers:
            raise ValueError(f"Unexpected peer identity: {peer_identity}")

        peer_public_key = self.trusted_peers[peer_identity]

        message = self.peer_role.encode() + self.th

        peer_public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )

        print(f"[*] {self.identity} verified Gateway RSA-PSS signature")


    def derive_session_keys(
        self,
        peer_dh_public_key: dh.DHPublicKey,
    ) -> SessionKeys:
        """
        Compute the DH shared secret and derive the session keys.
        """
        if self.dh_private_key is None:
            raise ValueError("Handshake has not been initialized")

        if self.th is None:
            raise ValueError("Transcript hash has not been computed")

        if len(self.th) != 32:
            raise ValueError("Transcript hash must be 32 bytes")

        shared_secret = self.dh_private_key.exchange(peer_dh_public_key)

        if len(shared_secret) > DH_VALUE_SIZE:
            raise ValueError("DH shared secret is larger than expected")

        z = shared_secret.rjust(DH_VALUE_SIZE, b"\x00")

        keys = kdf(z, self.th)

        print(f"[*] {self.identity} derived session keys")

        return keys


def handshake(gateway: Party, node: Party) -> tuple[Session, Session]:
    """
    Perform the handshake between the gateway and node. 
    returns the established sessions for each party.
    """
    print(f"\nBeginning handshake between Gateway and Node")
    print(f"{'=' * 60}")

    gateway_hello = gateway.hello()
    node_hello = node.hello()

    gateway_transcript = build_transcript(
        gateway.identity,
        node_hello.identity,
        gateway.dh_public_key,
        node_hello.dh_public_key,
        gateway.nonce,
        node_hello.nonce
    )

    print(f"[*] {GATEWAY_IDENTITY} constructed transcript")

    node_transcript = build_transcript(
        gateway_hello.identity,
        node.identity,
        gateway_hello.dh_public_key,
        node.dh_public_key,
        gateway_hello.nonce,
        node.nonce
    )

    print(f"[*] {NODE_IDENTITY} constructed transcript")

    gateway_th = gateway.hash_transcript(gateway_transcript)
    node_th = node.hash_transcript(node_transcript)

    assert gateway_th == node_th

    print(f"[*] Transcript hashes match")
    
    gateway_signature = gateway.sign()
    node_signature = node.sign()

    gateway.verify_signature(
        peer_identity=node_hello.identity,
        signature=node_signature,
    )
    node.verify_signature(
        peer_identity=gateway_hello.identity,
        signature=gateway_signature,
    )

    gateway_keys = gateway.derive_session_keys(
        node_hello.dh_public_key,
    )
    node_keys = node.derive_session_keys(
        gateway_hello.dh_public_key,
    )

    gateway_session = Session(
        session_id=gateway_keys.session_id,
        send_enc_key=gateway_keys.g2n_enc,
        send_mac_key=gateway_keys.g2n_mac,
        recv_enc_key=gateway_keys.n2g_enc,
        recv_mac_key=gateway_keys.n2g_mac
    )

    node_session = Session(
        session_id=node_keys.session_id,
        send_enc_key=node_keys.n2g_enc,
        send_mac_key=node_keys.n2g_mac,
        recv_enc_key=node_keys.g2n_enc,
        recv_mac_key=node_keys.g2n_mac
    )

    assert gateway_keys.session_id == node_keys.session_id

    print(f"[*] Session IDs match: {node_keys.session_id.hex()}")

    assert gateway_session.send_enc_key == node_session.recv_enc_key
    assert gateway_session.send_mac_key == node_session.recv_mac_key

    print(f"[*] Gateway send keys match Node receive keys")

    assert node_session.send_enc_key == gateway_session.recv_enc_key
    assert node_session.send_mac_key == gateway_session.recv_mac_key

    print(f"[*] Node send keys match Gateway receive keys")

    print(f"[*] Sessions established successfully")

    return gateway_session, node_session


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
