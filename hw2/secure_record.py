import struct

from cryptography.exceptions import InvalidSignature
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


class RecordError(Exception):
    pass


class AuthenticationError(RecordError):
    pass


class SequenceError(RecordError):
    pass


class DirectionError(RecordError):
    pass


def parse_header(record: bytes, ciphertext_length: int) -> tuple[bytes, bytes]:
    iv_start = HEADER_SIZE
    iv_end = iv_start + IV_SIZE

    iv = record[iv_start:iv_end]

    ct_start = iv_end
    ct_end = ct_start + ciphertext_length

    ciphertext = record[ct_start:ct_end]
    tag = record[ct_end:]

    return iv, ciphertext, tag


def validate_record(record: bytes, ciphertext_length: int) -> None:
    expected_record_length = (
        HEADER_SIZE
        + IV_SIZE
        + ciphertext_length
        + TAG_SIZE
    )

    if len(record) != expected_record_length:
        raise RecordError("Malformed record")


def verify_hmac(
    session: Session,
    header: bytes,
    iv: bytes,
    ciphertext: bytes,
    tag: bytes,
) -> None:
    mac = hmac.HMAC(
        session.recv_mac_key,
        hashes.SHA256(),
    )

    mac.update(header)
    mac.update(iv)
    mac.update(ciphertext)

    try:
        mac.verify(tag)
    except InvalidSignature:
        raise AuthenticationError("Invalid record authentication tag")


def decrypt_ciphertext(session: Session, iv: bytes, ciphertext: bytes) -> bytes:
    cipher = Cipher(
        algorithms.AES(session.recv_enc_key),
        modes.CTR(iv),
    )

    decryptor = cipher.decryptor()

    return (
        decryptor.update(ciphertext)
        + decryptor.finalize()
    )


def open_record(
    session: Session,
    record: bytes,
) -> tuple[bytes, bytes]:
    """
    Verify and decrypt a record.

    Returns:
        bytes: messge_type
        bytes: plaintext
    """
    print(f"\n{'=' * 60}")
    print("OPENING RECORD")
    print(f"{'=' * 60}")

    header = record[:HEADER_SIZE]

    (
        version,
        direction,
        sequence,
        message_type,
        ciphertext_length,
    ) = HEADER_STRUCT.unpack(header)

    iv, ciphertext, tag = parse_header(record, ciphertext_length)

    validate_record(record, ciphertext_length)
    verify_hmac(
        session=session,
        header=header,
        iv=iv,
        ciphertext=ciphertext,
        tag=tag
    )

    if version != VERSION:
        raise RecordError("Unsupported version")

    if direction != session.recv_direction:
        raise DirectionError("Wrong record direction")

    if sequence != session.recv_sequence:
        raise SequenceError(f"Expected sequence {session.recv_sequence}, got {sequence}")

    expected_iv = session.session_id + sequence.to_bytes(8, "big")

    if iv != expected_iv:
        raise RecordError("Invalid IV")

    plaintext = decrypt_ciphertext(session, iv, ciphertext)

    session.recv_sequence += 1

    return message_type, plaintext


def seal(
    session: Session,
    plaintext: bytes,
    message_type: int,
) -> bytes:
    """
    Encrypt a plaintext record
    
    Returns:
        bytes: record
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

    message = b'Hello, Node'

    record = seal(gateway_session, message, 1)
    message_type, plaintext = open_record(node_session, record)

    print(message.decode())
    print(plaintext.decode())

    print("")


if __name__ == "__main__":
    main()
