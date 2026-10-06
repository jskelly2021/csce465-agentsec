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
    """
    Verify and decrypt a record. Return the decrypted plaintext and messge type.
    """
    pass


def seal(
    session: Session,
    plaintext: bytes,
    message_type: int,
) -> bytes:
    """
    Encrypt a plaintext record. Return the encrypted record.
    """
    sequence = session.send_sequence

    print(f"\n{'=' * 60}")
    print("SEALING RECORD")
    print(f"{'-' * 60}")
    print(f"Plaintext: {plaintext!r}")
    print(f"Plaintext length: {len(plaintext)} bytes")
    print(f"Message type: {message_type}")
    print(f"Send sequence: {sequence}")
    print(f"{'=' * 60}")


    iv = session.session_id + sequence.to_bytes(8, 'big')

    header = HEADER_STRUCT.pack(
        VERSION,
        session.send_direction,
        sequence,
        message_type,
        len(plaintext),
    )

    cipher = Cipher(
        algorithms.AES(session.send_enc_key),
        modes.CTR(iv),
    )

    encryptor = cipher.encryptor()

    ciphertext = (
        encryptor.update(plaintext)
        + encryptor.finalize()
    )

    mac = hmac.HMAC(
        session.send_mac_key,
        hashes.SHA256(),
    )
    mac.update(header + iv + ciphertext)
    tag = mac.finalize()

    record = header + iv + ciphertext + tag

    print(f"[*] Session ID: {session.session_id.hex()}")
    print(f"[*] IV: {iv.hex()}")
    print(f"[*] IV length: {len(iv)} bytes")

    print(f"[*] Header: {header.hex()}")
    print(f"[*] Header length: {len(header)} bytes")

    print(f"[*] Ciphertext: {ciphertext.hex()}")
    print(f"[*] Ciphertext length: {len(ciphertext)} bytes")

    print(f"[*] MAC input length: {len(header + iv + ciphertext)} bytes")
    print(f"[*] HMAC tag: {tag.hex()}")
    print(f"[*] Tag length: {len(tag)} bytes")

    print(f"[*] Total record length: {len(record)} bytes")

    session.send_sequence += 1

    print(
        f"[*] Send sequence incremented: "
        f"{sequence} -> {session.send_sequence}"
    )

    print("[+] Record sealed successfully")

    return record


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

    record = seal(gateway_session, b'Hello, Node', 1)
    record = seal(gateway_session, b'Hello, Node, again', 1)

    print("")


if __name__ == "__main__":
    main()
