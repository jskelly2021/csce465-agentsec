import pytest

from secure_record import (
    seal,
    open_record,
    AuthenticationError,
    DirectionError,
    SequenceError,
    HEADER_SIZE,
    IV_SIZE,
)


def test_valid_bidirectional_messages(sessions):
    gateway_session, node_session = sessions

    gateway_message = b"Hello, Node"
    record = seal(
        gateway_session,
        gateway_message,
        message_type=1,
    )

    message_type, plaintext = open_record(
        node_session,
        record,
    )

    assert message_type == 1
    assert plaintext == gateway_message

    node_message = b"Hello, Gateway"
    record = seal(
        node_session,
        node_message,
        message_type=2,
    )

    message_type, plaintext = open_record(
        gateway_session,
        record,
    )

    assert message_type == 2
    assert plaintext == node_message


def test_modified_ciphertext_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"important command",
        message_type=1,
    )

    tampered = bytearray(record)

    ciphertext_start = HEADER_SIZE + IV_SIZE
    tampered[ciphertext_start] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(tampered))


def test_modified_header_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"hello",
        message_type=1,
    )

    tampered = bytearray(record)

    # Change authenticated message_type.
    tampered[10] ^= 0x01

    with pytest.raises(AuthenticationError):
        open_record(node_session, bytes(tampered))


def test_reflected_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"gateway command",
        message_type=1,
    )

    # Attacker reflects Gateway's own outgoing record back toward Gateway.
    with pytest.raises(DirectionError):
        open_record(gateway_session, record)


def test_replayed_record_rejected(sessions):
    gateway_session, node_session = sessions

    record = seal(
        gateway_session,
        b"perform action",
        message_type=1,
    )

    # First delivery is legitimate.
    _, plaintext = open_record(
        node_session,
        record,
    )

    assert plaintext == b"perform action"

    # Exact same authenticated record is replayed.
    with pytest.raises(SequenceError):
        open_record(node_session, record)
